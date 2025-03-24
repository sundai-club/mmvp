# Speech2Text for Cursor IDE

## Project Overview

A Next.js + Vite application that captures audio input, converts it to text in real-time, and pipes the output directly into the Cursor IDE chat interface, enabling voice-driven coding and interaction with Cursor's AI assistant.

## Key Features

- **Real-time Speech Recognition**: Convert spoken words to text with minimal latency
- **Cursor IDE Integration**: Seamlessly pipe text output into Cursor's chat input
- **Voice Command Recognition**: Special commands for common IDE operations
- **Transcription History**: Save and browse previous voice sessions
- **Customizable Settings**: Adjust sensitivity, language, and other parameters
- **Cross-Platform Support**: Works on major operating systems where Cursor runs
- **Local Whisper Implementation**: Process speech locally without relying on external APIs

## Technical Architecture

### Frontend (Next.js + Vite)
- **UI Components**: Minimal interface with recording controls and status indicators
- **Real-time Feedback**: Visual indicators for audio levels and recognition status
- **Settings Panel**: User preferences and configuration options

### Speech Recognition
- **Browser Web Speech API**: For basic recognition capabilities
- **Local Whisper Implementation**: Self-hosted model for privacy and offline use
  - Using Whisper.cpp or similar optimized implementation
  - Pre-trained models loaded and run in browser with WebAssembly
- **OpenAI Whisper API (Fallback)**: Optional cloud-based processing for enhanced accuracy
- **Offline Mode**: Complete offline operation using TensorFlow.js

### Cursor IDE Integration
- **Browser Extension**: To interact with Cursor if used in browser
- **Native Integration**: For Cursor desktop application
- **WebSocket Communication**: Real-time data transfer between application and IDE

## Implementation Plan

### Phase 1: Core Speech Recognition (Weeks 1-2)
- Set up Next.js + Vite project structure
- Implement basic UI with recording controls
- Integrate Web Speech API for basic recognition
- Add real-time transcription display
- Set up audio recording and processing pipeline

### Phase 2: Local Whisper Implementation (Weeks 3-4)
- Integrate local Whisper models using WebAssembly
- Implement model loading and optimization for browser environment
- Add support for different model sizes (tiny, base, small, medium)
- Create efficient audio processing pipeline
- Implement caching mechanisms for improved performance

### Phase 3: Enhanced Recognition Features (Weeks 5-6)
- Add language detection and multi-language support
- Implement noise filtering and accuracy improvements
- Develop transcription history and management
- Add fallback to OpenAI Whisper API when needed
- Optimize for technical and coding terminology

### Phase 4: Cursor IDE Integration (Weeks 7-8)
- Research Cursor IDE's API/extension capabilities
- Develop method to pipe text into Cursor's chat input
- Implement special voice commands for IDE operations
- Create browser extension or native integration component

### Phase 5: Testing & Refinement (Weeks 9-10)
- Comprehensive testing across platforms
- Performance optimization for reduced latency
- User feedback incorporation
- Documentation and tutorials

## Technical Requirements

### Dependencies
- Next.js 14+
- Vite 5+
- React 18+
- FFmpeg-wasm for audio processing
- OpenAI API client (optional for API fallback)
- Web Speech API
- TensorFlow.js (for model inference)
- WebAssembly support for Whisper.cpp
- WebSocket libraries

### Development Environment
- Node.js 18+
- Typescript 5+
- ESLint and Prettier for code quality
- Jest for testing

### Deployment
- Vercel for hosting the web application
- Chrome Web Store for browser extension
- GitHub for version control and collaboration

## Getting Started (For Developers)

```bash
# Clone the repository
git clone [repository-url]

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API keys if using OpenAI fallback

# Start development server
npm run dev
```

## Implementing Local Whisper

The local Whisper implementation will use WebAssembly to run the model directly in the browser:

1. **Model Loading**: Pre-trained Whisper models will be converted to a format suitable for browser execution
2. **Audio Processing**: 
   - Capture audio using the MediaRecorder API
   - Convert audio to the required format (16kHz mono WAV)
   - Process in chunks for real-time transcription
3. **Inference Pipeline**:
   - Audio chunking and preprocessing
   - Model inference using WebAssembly
   - Post-processing and text formatting
4. **Optimization Techniques**:
   - Quantized models for smaller size and faster inference
   - Web Worker implementation for non-blocking operation
   - Streaming inference for real-time results

## Example Implementation Structure

```typescript
// Audio recording component
const AudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const whisperModelRef = useRef<WhisperModel | null>(null);
  
  useEffect(() => {
    // Initialize Whisper model
    const initWhisper = async () => {
      const model = await WhisperModel.load('/models/whisper-tiny.bin');
      whisperModelRef.current = model;
    };
    
    initWhisper();
    
    return () => {
      whisperModelRef.current?.dispose();
    };
  }, []);
  
  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        setAudioChunks((prev) => [...prev, event.data]);
        
        // Process chunk with Whisper for streaming results
        processAudioChunk(event.data);
      }
    };
    
    mediaRecorder.start(1000); // Collect data in 1-second chunks
    mediaRecorderRef.current = mediaRecorder;
    setIsRecording(true);
  };
  
  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    // Process complete audio for final transcript
    processCompleteAudio(audioChunks);
  };
  
  // Process audio with local Whisper model
  const processAudioChunk = async (chunk: Blob) => {
    if (!whisperModelRef.current) return;
    
    const arrayBuffer = await chunk.arrayBuffer();
    const result = await whisperModelRef.current.transcribe(arrayBuffer);
    
    // Update UI with transcript
    updateTranscript(result.text);
  };
  
  // ...rest of component
};
```

## Reference Projects

This project draws inspiration and technical approaches from:

- [nextjs-whisper](https://github.com/snettah/nextjs-whisper) - Implementation of Whisper with Next.js 13
- [chatgpt-whisper-nextjs](https://github.com/coryshaw/chatgpt-whisper-nextjs) - Demo combining ChatGPT and Whisper APIs

## Challenges and Considerations

- **Latency**: Minimizing delay between speech and text output, especially with local processing
- **Model Size**: Balancing model size vs. accuracy for browser-based inference
- **Memory Usage**: Managing memory usage during model inference
- **Accuracy**: Ensuring correct transcription, especially for technical terms
- **IDE Integration**: Finding the right approach to interact with Cursor
- **Privacy**: Handling voice data securely and with user consent
- **Cross-platform**: Ensuring consistent experience across operating systems

## Future Enhancements

- **Custom Voice Models**: Train on coding terminology for improved accuracy
- **Code Snippet Detection**: Automatically format spoken code
- **Multi-user Support**: Collaborative voice coding sessions
- **Voice Profiles**: Per-user settings and customizations
- **Language-specific Models**: Optimized for different programming languages
- **Fine-tuned Models**: Specialized models for programming terminology

## Troubleshooting

If you encounter issues while implementing this project, here are some tips:

1. **Audio Recording Issues**:
   - Ensure browser permissions are granted for microphone access
   - Verify MediaRecorder API compatibility with your browser
   - Try different audio formats if processing fails

2. **Model Loading Problems**:
   - Check that WebAssembly is supported in your browser
   - Verify model file paths and formats
   - Try smaller models if memory issues occur

3. **Integration Challenges**:
   - Add console.log statements to debug the pipeline
   - Ensure the audio format matches what Whisper expects
   - Check browser console for errors during model inference

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to participate in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
