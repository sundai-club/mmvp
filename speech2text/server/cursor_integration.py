#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cursor IDE Integration for Speech2Text

This script provides integration between the Speech2Text server and Cursor IDE.
It allows sending transcribed text directly to Cursor's chat input.
"""

import argparse
import json
import logging
import os
import sys
import threading
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

import websocket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CursorIntegration:
    """Integration with Cursor IDE"""
    
    def __init__(self, server_host="127.0.0.1", server_port=5000, 
                 ws_port=5001, callback_port=5002):
        """Initialize Cursor integration"""
        self.server_host = server_host
        self.server_port = server_port
        self.ws_port = ws_port
        self.callback_port = callback_port
        self.ws = None
        self.callback_server = None
        self.last_text = ""
        self.is_connected = False
        
    def start_ws_client(self):
        """Start WebSocket client to receive transcriptions"""
        ws_url = f"ws://{self.server_host}:{self.ws_port}"
        logger.info(f"Connecting to WebSocket server at {ws_url}")
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("type") == "transcription":
                    text = data.get("text", "")
                    if text and text != self.last_text:
                        self.last_text = text
                        logger.info(f"Received transcription: {text}")
                        # Send to Cursor IDE
                        self.send_to_cursor(text)
                elif data.get("type") == "status":
                    logger.info(f"Status: {data.get('message')}")
                elif data.get("type") == "error":
                    logger.error(f"Error: {data.get('message')}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse message: {message}")
        
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed")
            self.is_connected = False
        
        def on_open(ws):
            logger.info("WebSocket connection established")
            self.is_connected = True
            # Send configuration
            ws.send(json.dumps({
                "type": "config",
                "model": "tiny"  # Use tiny model for faster response
            }))
        
        # Create WebSocket connection
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Start WebSocket client in a thread
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
    
    def send_to_cursor(self, text):
        """Send text to Cursor IDE via callback server"""
        # This would normally communicate with the Cursor IDE extension
        # For now, we just log it
        logger.info(f"Sending to Cursor: {text}")
        
        # In a real implementation, this would communicate with a browser extension
        # or native integration with Cursor IDE
    
    def start_callback_server(self):
        """Start HTTP server to receive callbacks from Cursor IDE"""
        
        class CallbackHandler(BaseHTTPRequestHandler):
            """Handler for callback HTTP server"""
            
            def do_POST(self):
                """Handle POST requests"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    logger.info(f"Received callback from Cursor: {data}")
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse callback data: {post_data}")
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error"}).encode('utf-8'))
            
            def log_message(self, format, *args):
                """Override log_message to use our logger"""
                logger.debug(format % args)
        
        # Start HTTP server in a thread
        self.callback_server = HTTPServer((self.server_host, self.callback_port), CallbackHandler)
        server_thread = threading.Thread(target=self.callback_server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        logger.info(f"Callback server started at http://{self.server_host}:{self.callback_port}")
    
    def open_demo_page(self):
        """Open demo page in browser"""
        url = f"http://{self.server_host}:{self.server_port}/stream"
        logger.info(f"Opening demo page at {url}")
        webbrowser.open(url)
    
    def stop(self):
        """Stop all services"""
        if self.ws:
            self.ws.close()
        
        if self.callback_server:
            self.callback_server.shutdown()
            self.callback_server.server_close()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Cursor IDE Integration for Speech2Text")
    parser.add_argument("--server-host", type=str, default="127.0.0.1",
                        help="Host of the Speech2Text server (default: 127.0.0.1)")
    parser.add_argument("--server-port", type=int, default=5000,
                        help="Port of the Speech2Text HTTP server (default: 5000)")
    parser.add_argument("--ws-port", type=int, default=5001,
                        help="Port of the Speech2Text WebSocket server (default: 5001)")
    parser.add_argument("--callback-port", type=int, default=5002,
                        help="Port for the callback server (default: 5002)")
    parser.add_argument("--demo", action="store_true",
                        help="Open demo page in browser")
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    
    # Create Cursor integration
    integration = CursorIntegration(
        server_host=args.server_host,
        server_port=args.server_port,
        ws_port=args.ws_port,
        callback_port=args.callback_port
    )
    
    try:
        # Start services
        integration.start_callback_server()
        integration.start_ws_client()
        
        # Open demo page if requested
        if args.demo:
            time.sleep(1)  # Wait for services to start
            integration.open_demo_page()
        
        # Keep running until interrupted
        logger.info("Press Ctrl+C to stop")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        integration.stop()

if __name__ == "__main__":
    main() 