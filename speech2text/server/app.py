#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
import base64
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from pydub import AudioSegment
from dotenv import load_dotenv

from whisper_service import WhisperService
from websocket_service import start_websocket_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Whisper service
whisper_service = WhisperService()

# Configure server settings
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 5000))
WEBSOCKET_PORT = int(os.getenv('WEBSOCKET_PORT', 5001))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    model_status = "loaded" if whisper_service.is_model_loaded() else "not loaded"
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "model_status": model_status,
        "torch_device": str(whisper_service.device)
    })

@app.route('/models', methods=['GET'])
def list_models():
    """List available models"""
    return jsonify({
        "available_models": whisper_service.list_available_models()
    })

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio data endpoint
    
    Expects:
    - audio_data: base64 encoded audio data
    - model_name: (optional) name of the model to use
    - language: (optional) language code
    """
    try:
        data = request.get_json()
        
        if not data or 'audio_data' not in data:
            return jsonify({"error": "Missing audio data"}), 400
        
        # Get options from request
        audio_data_b64 = data['audio_data']
        model_name = data.get('model_name', 'base')
        language = data.get('language')
        
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_data_b64.split(',')[1] 
                                         if ',' in audio_data_b64 
                                         else audio_data_b64)
        except Exception as e:
            return jsonify({"error": f"Failed to decode audio data: {str(e)}"}), 400
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_bytes)
        
        try:
            # Convert to WAV if needed
            if not temp_path.endswith('.wav'):
                wav_path = temp_path.replace('.webm', '.wav')
                audio = AudioSegment.from_file(temp_path)
                audio.export(wav_path, format="wav")
                os.remove(temp_path)
                temp_path = wav_path
            
            # Transcribe audio
            result = whisper_service.transcribe(
                audio_path=temp_path,
                model_name=model_name,
                language=language
            )
            
            return jsonify(result)
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.exception("Error processing transcription request")
        return jsonify({"error": str(e)}), 500

@app.route('/stream', methods=['GET'])
def stream_page():
    """Return HTML page for WebSocket streaming demo"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Speech2Text - Streaming Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            button { padding: 10px 20px; margin: 10px 0; }
            #transcript { border: 1px solid #ccc; padding: 10px; min-height: 200px; margin-top: 20px; }
            .controls { display: flex; gap: 10px; }
            #audio-level { width: 100%; height: 20px; background: #eee; margin-top: 10px; }
            #level-indicator { height: 20px; width: 0%; background: #4CAF50; transition: width 0.1s; }
        </style>
    </head>
    <body>
        <h1>Speech2Text - Streaming Demo</h1>
        <div class="controls">
            <button id="start-btn">Start Recording</button>
            <button id="stop-btn" disabled>Stop Recording</button>
            <select id="model-select">
                <option value="tiny">Tiny (fast)</option>
                <option value="base" selected>Base (balanced)</option>
                <option value="small">Small (better quality)</option>
                <option value="medium">Medium (high quality)</option>
            </select>
        </div>
        <div id="audio-level">
            <div id="level-indicator"></div>
        </div>
        <div id="status">Status: Ready</div>
        <h2>Transcript</h2>
        <div id="transcript"></div>
        
        <script>
            const startBtn = document.getElementById('start-btn');
            const stopBtn = document.getElementById('stop-btn');
            const modelSelect = document.getElementById('model-select');
            const transcriptDiv = document.getElementById('transcript');
            const statusDiv = document.getElementById('status');
            const levelIndicator = document.getElementById('level-indicator');
            
            let mediaRecorder;
            let audioChunks = [];
            let ws;
            let audioContext;
            let analyser;
            let microphone;
            
            startBtn.addEventListener('click', async () => {
                try {
                    // Create WebSocket connection
                    ws = new WebSocket(`ws://${window.location.hostname}:${window.location.port.replace('5000', '5001')}`);
                    
                    ws.onopen = async () => {
                        // Send configuration
                        ws.send(JSON.stringify({
                            type: 'config',
                            model: modelSelect.value
                        }));
                        
                        // Start recording
                        statusDiv.textContent = 'Status: Connecting to microphone...';
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        
                        // Set up audio level visualization
                        setupAudioVisualization(stream);
                        
                        mediaRecorder = new MediaRecorder(stream);
                        audioChunks = [];
                        
                        mediaRecorder.ondataavailable = (event) => {
                            if (event.data.size > 0) {
                                audioChunks.push(event.data);
                                
                                // Send audio chunk to server
                                const reader = new FileReader();
                                reader.onloadend = () => {
                                    const base64data = reader.result;
                                    ws.send(JSON.stringify({
                                        type: 'audio_chunk',
                                        data: base64data
                                    }));
                                };
                                reader.readAsDataURL(event.data);
                            }
                        };
                        
                        ws.onmessage = (event) => {
                            const data = JSON.parse(event.data);
                            if (data.type === 'transcription') {
                                transcriptDiv.textContent = data.text;
                            } else if (data.type === 'status') {
                                statusDiv.textContent = `Status: ${data.message}`;
                            }
                        };
                        
                        mediaRecorder.start(1000);
                        startBtn.disabled = true;
                        stopBtn.disabled = false;
                        statusDiv.textContent = 'Status: Recording...';
                    };
                    
                    ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        statusDiv.textContent = 'Status: WebSocket error. See console for details.';
                    };
                    
                    ws.onclose = () => {
                        statusDiv.textContent = 'Status: Connection closed';
                        startBtn.disabled = false;
                        stopBtn.disabled = true;
                    };
                    
                } catch (error) {
                    console.error('Error starting recording:', error);
                    statusDiv.textContent = `Status: Error - ${error.message}`;
                }
            });
            
            stopBtn.addEventListener('click', () => {
                if (mediaRecorder) {
                    mediaRecorder.stop();
                    
                    if (audioContext) {
                        audioContext.close();
                        audioContext = null;
                        analyser = null;
                        microphone = null;
                    }
                    
                    // Stop all tracks on the stream
                    mediaRecorder.stream.getTracks().forEach(track => track.stop());
                }
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'stop' }));
                    ws.close();
                }
                
                startBtn.disabled = false;
                stopBtn.disabled = true;
                statusDiv.textContent = 'Status: Stopped';
                levelIndicator.style.width = '0%';
            });
            
            function setupAudioVisualization(stream) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                microphone = audioContext.createMediaStreamSource(stream);
                
                microphone.connect(analyser);
                analyser.fftSize = 256;
                
                const bufferLength = analyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);
                
                function updateLevel() {
                    if (!analyser) return;
                    
                    analyser.getByteFrequencyData(dataArray);
                    const average = dataArray.reduce((a, b) => a + b, 0) / bufferLength;
                    const level = Math.min(100, average * 2);
                    
                    levelIndicator.style.width = `${level}%`;
                    levelIndicator.style.background = level > 50 ? '#FF4136' : '#4CAF50';
                    
                    if (audioContext) {
                        requestAnimationFrame(updateLevel);
                    }
                }
                
                updateLevel();
            }
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Start WebSocket server in a separate thread
    import threading
    websocket_thread = threading.Thread(
        target=start_websocket_server,
        args=(HOST, WEBSOCKET_PORT, whisper_service),
        daemon=True
    )
    websocket_thread.start()
    
    logger.info(f"Starting server on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=True) 