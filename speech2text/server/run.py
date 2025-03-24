#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Speech2Text Server for Cursor IDE

This script starts the Flask server and WebSocket server for the Speech2Text application.
"""

import argparse
import logging
import os
import sys

# Add the current directory to the path so that imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, HOST, PORT, WEBSOCKET_PORT, start_websocket_server, whisper_service

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Speech2Text Server for Cursor IDE")
    parser.add_argument("--host", type=str, default=HOST,
                        help=f"Host to run the server on (default: {HOST})")
    parser.add_argument("--port", type=int, default=PORT,
                        help=f"Port to run the HTTP server on (default: {PORT})")
    parser.add_argument("--ws-port", type=int, default=WEBSOCKET_PORT,
                        help=f"Port to run the WebSocket server on (default: {WEBSOCKET_PORT})")
    parser.add_argument("--model", type=str, default="base",
                        help="Whisper model to preload (default: base)")
    parser.add_argument("--debug", action="store_true",
                        help="Run in debug mode")
    parser.add_argument("--no-preload", action="store_true",
                        help="Don't preload the Whisper model")
    
    return parser.parse_args()

def setup_logging(debug):
    """Set up logging"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main function"""
    args = parse_args()
    setup_logging(args.debug)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Speech2Text server")
    
    # Preload the model if requested
    if not args.no_preload:
        logger.info(f"Preloading Whisper model: {args.model}")
        whisper_service._load_model(args.model)
    
    # Start WebSocket server in a separate thread
    import threading
    websocket_thread = threading.Thread(
        target=start_websocket_server,
        args=(args.host, args.ws_port, whisper_service),
        daemon=True
    )
    websocket_thread.start()
    
    # Start the Flask server
    logger.info(f"Starting HTTP server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main() 