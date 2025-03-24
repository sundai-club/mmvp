# Speech2Text Python Server

A local Python server implementation that provides speech-to-text transcription using OpenAI's Whisper model.

## Features

- **Local Whisper Processing**: Completely offline speech recognition
- **Real-time Transcription**: Stream audio for immediate feedback
- **Multiple Model Sizes**: Choose from tiny, base, small, medium, or large models
- **WebSocket Streaming**: Low-latency audio processing
- **Cursor IDE Integration**: Send transcriptions to Cursor IDE

## Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

## Usage

### Starting the Server

```bash
python run.py
```

This will start both the HTTP server and WebSocket server. The HTTP server provides REST APIs for transcription, while the WebSocket server enables real-time audio streaming.

### Command-line Options

```bash
python run.py --help
```

Available options:
- `--host`: Host to run the server on (default: 127.0.0.1)
- `--port`: Port for the HTTP server (default: 5000)
- `--ws-port`: Port for the WebSocket server (default: 5001)
- `--model`: Whisper model to preload (default: base)
- `--debug`: Run in debug mode
- `--no-preload`: Don't preload the Whisper model

### API Endpoints

- **GET /health**: Health check endpoint
- **GET /models**: List available Whisper models
- **POST /transcribe**: Transcribe audio data
- **GET /stream**: Web interface for testing WebSocket streaming

### WebSocket API

The WebSocket server accepts the following message types:

1. **Configuration**:
   ```json
   {
     "type": "config",
     "model": "base",
     "language": "en"
   }
   ```

2. **Audio Chunk**:
   ```json
   {
     "type": "audio_chunk",
     "data": "base64_encoded_audio_data"
   }
   ```

3. **Stop**:
   ```json
   {
     "type": "stop"
   }
   ```

## Cursor IDE Integration

The `cursor_integration.py` script connects the speech-to-text server with Cursor IDE.

```bash
python cursor_integration.py --demo
```

This will:
1. Connect to the WebSocket server
2. Start a callback HTTP server for Cursor integration
3. Open the demo streaming page in your browser

## Model Information

This server uses OpenAI's Whisper models for transcription:

| Model | Parameters | Required VRAM | Relative Speed |
|-------|------------|--------------|----------------|
| tiny  | 39 M       | ~1 GB        | ~32x           |
| base  | 74 M       | ~1 GB        | ~16x           |
| small | 244 M      | ~2 GB        | ~6x            |
| medium| 769 M      | ~5 GB        | ~2x            |
| large | 1550 M     | ~10 GB       | 1x             |

The first time you use a model, it will be downloaded automatically.

## Troubleshooting

- **Audio not being transcribed**: Check microphone permissions and that the audio format is supported.
- **Slow transcription**: Try using a smaller model like "tiny" or "base" instead of "medium" or "large".
- **Memory issues**: GPU memory might be insufficient for larger models. Use a smaller model or switch to CPU with `CUDA_VISIBLE_DEVICES=-1`.
- **Connection errors**: Ensure ports are not in use by other applications.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 