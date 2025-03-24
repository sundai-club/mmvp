#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import base64
import json
import logging
import os
import tempfile
import time
import uuid
from typing import Dict, Any, List, Optional

import websockets
from pydub import AudioSegment
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure FFmpeg path
FFMPEG_PATH = os.getenv('FFMPEG_PATH')
if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
    AudioSegment.converter = FFMPEG_PATH
    logger.info(f"Using FFmpeg from: {FFMPEG_PATH}")
else:
    logger.warning("FFmpeg path not set or invalid. Please install FFmpeg and add to PATH or set FFMPEG_PATH in .env")

# Global dictionary to store active connections
active_connections = {}

class WebSocketHandler:
    """Handler for WebSocket connections"""
    
    def __init__(self, websocket, path, whisper_service):
        """Initialize WebSocket handler"""
        self.websocket = websocket
        self.path = path
        self.whisper_service = whisper_service
        self.session_id = str(uuid.uuid4())
        self.temp_dir = tempfile.mkdtemp()
        self.chunks = []
        self.chunk_count = 0
        self.model_name = "base"
        self.language = None
        self.is_streaming = False
        self.last_transcription = ""
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logger.info(f"New WebSocket connection: {self.session_id}")
    
    async def send_status(self, message: str):
        """Send status message to client"""
        await self.websocket.send(json.dumps({
            "type": "status",
            "message": message
        }))
    
    async def send_transcription(self, text: str):
        """Send transcription to client"""
        await self.websocket.send(json.dumps({
            "type": "transcription",
            "text": text
        }))
    
    async def send_error(self, error: str):
        """Send error message to client"""
        await self.websocket.send(json.dumps({
            "type": "error",
            "message": error
        }))
    
    async def handle_config(self, data: Dict[str, Any]):
        """Handle configuration message from client"""
        if 'model' in data:
            self.model_name = data['model']
            logger.info(f"Session {self.session_id} - Using model: {self.model_name}")
            
        if 'language' in data:
            self.language = data['language']
            logger.info(f"Session {self.session_id} - Using language: {self.language}")
            
        # Preload the model
        try:
            self.whisper_service._load_model(self.model_name)
            await self.send_status(f"Model '{self.model_name}' loaded")
        except Exception as e:
            logger.exception(f"Error loading model: {str(e)}")
            await self.send_error(f"Failed to load model: {str(e)}")
    
    async def handle_audio_chunk(self, data: Dict[str, Any]):
        """Handle audio chunk from client"""
        try:
            # Decode base64 audio data
            audio_data_b64 = data['data']
            audio_bytes = base64.b64decode(audio_data_b64.split(',')[1] 
                                        if ',' in audio_data_b64 
                                        else audio_data_b64)
            
            # Create chunk file path
            chunk_path = os.path.join(self.temp_dir, f"chunk_{self.chunk_count}.webm")
            
            # Save chunk to file
            with open(chunk_path, 'wb') as f:
                f.write(audio_bytes)
            
            # Add to list of chunks
            self.chunks.append(chunk_path)
            self.chunk_count += 1
            
            # If this is the first chunk or we have a certain number of chunks, start transcription
            if self.chunk_count % 3 == 0 or self.chunk_count == 1:
                asyncio.create_task(self.transcribe_chunks())
            
        except Exception as e:
            logger.exception(f"Error processing audio chunk: {str(e)}")
            await self.send_error(f"Error processing audio chunk: {str(e)}")
    
    async def transcribe_chunks(self):
        """Transcribe collected audio chunks"""
        if not self.chunks:
            return
        
        try:
            # Create combined audio file
            combined_path = os.path.join(self.temp_dir, "combined.wav")
            
            # Process first chunk
            audio = AudioSegment.from_file(self.chunks[0])
            
            # Add other chunks if they exist
            for chunk_path in self.chunks[1:]:
                try:
                    chunk_audio = AudioSegment.from_file(chunk_path)
                    audio += chunk_audio
                except Exception as e:
                    logger.warning(f"Error processing chunk {chunk_path}: {str(e)}")
            
            # Export as WAV for Whisper
            audio.export(combined_path, format="wav")
            
            # Transcribe audio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.whisper_service.transcribe_chunk(
                    audio_path=combined_path,
                    model_name=self.model_name,
                    language=self.language
                )
            )
            
            # Send transcription to client
            text = result.get("text", "").strip()
            if text and text != self.last_transcription:
                self.last_transcription = text
                await self.send_transcription(text)
                
        except Exception as e:
            logger.exception(f"Error transcribing chunks: {str(e)}")
            await self.send_error(f"Error transcribing audio: {str(e)}")
    
    async def handle_stop(self):
        """Handle stop message from client"""
        if self.chunks:
            # Final transcription of all chunks
            await self.transcribe_chunks()
        
        # Clean up temp files
        await self.cleanup()
    
    async def cleanup(self):
        """Clean up temporary files"""
        try:
            # Remove chunk files
            for chunk_path in self.chunks:
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)
            
            # Remove combined file
            combined_path = os.path.join(self.temp_dir, "combined.wav")
            if os.path.exists(combined_path):
                os.remove(combined_path)
            
            # Remove temp directory
            os.rmdir(self.temp_dir)
            
            logger.info(f"Cleaned up session {self.session_id}")
        except Exception as e:
            logger.exception(f"Error during cleanup: {str(e)}")
    
    async def handle(self):
        """Main handler for WebSocket connection"""
        try:
            # Register connection
            active_connections[self.session_id] = self
            
            # Send initial status
            await self.send_status("Connected")
            
            # Handle messages
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    
                    if message_type == 'config':
                        await self.handle_config(data)
                    elif message_type == 'audio_chunk':
                        await self.handle_audio_chunk(data)
                    elif message_type == 'stop':
                        await self.handle_stop()
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        
                except json.JSONDecodeError:
                    await self.send_error("Invalid JSON message")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed: {self.session_id}")
        
        except Exception as e:
            logger.exception(f"Error in WebSocket handler: {str(e)}")
        
        finally:
            # Clean up resources
            await self.cleanup()
            
            # Remove from active connections
            if self.session_id in active_connections:
                del active_connections[self.session_id]
            
            logger.info(f"WebSocket connection ended: {self.session_id}")

async def websocket_server(host, port, whisper_service):
    """Start WebSocket server"""
    async def handler(websocket, path):
        handler = WebSocketHandler(websocket, path, whisper_service)
        await handler.handle()
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    try:
        async with websockets.serve(handler, host, port):
            await asyncio.Future()  # Run forever
    except Exception as e:
        logger.exception(f"Error starting WebSocket server: {str(e)}")

def start_websocket_server(host, port, whisper_service):
    """Start WebSocket server in a separate thread"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(websocket_server(host, port, whisper_service))
    except Exception as e:
        logger.exception(f"Error in WebSocket server thread: {str(e)}")
    finally:
        loop.close() 