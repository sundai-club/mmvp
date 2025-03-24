#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import time
from typing import Dict, Any, Optional, List

import torch
import whisper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WhisperService:
    """Service for transcribing audio using local Whisper models"""
    
    # Available Whisper models
    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    
    def __init__(self):
        """Initialize the Whisper service"""
        self.models = {}  # Cache for loaded models
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing WhisperService with device: {self.device}")
        
        # Preload base model as default
        self._load_model("base")
    
    def _load_model(self, model_name: str):
        """
        Load a Whisper model
        
        Args:
            model_name: Name of the model to load (tiny, base, small, medium, large)
        
        Returns:
            The loaded model
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model_name}' not available. Choose from: {', '.join(self.AVAILABLE_MODELS)}")
        
        if model_name not in self.models:
            logger.info(f"Loading model: {model_name}")
            start_time = time.time()
            
            try:
                model = whisper.load_model(model_name, device=self.device)
                self.models[model_name] = model
                
                load_time = time.time() - start_time
                logger.info(f"Model '{model_name}' loaded in {load_time:.2f} seconds")
                
                return model
            except Exception as e:
                logger.exception(f"Error loading model '{model_name}': {str(e)}")
                raise
        else:
            logger.debug(f"Using cached model: {model_name}")
            return self.models[model_name]
    
    def list_available_models(self) -> List[str]:
        """
        Get list of available models
        
        Returns:
            List of available model names
        """
        return self.AVAILABLE_MODELS
    
    def is_model_loaded(self, model_name: str = "base") -> bool:
        """
        Check if a model is loaded
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if the model is loaded, False otherwise
        """
        return model_name in self.models
    
    def transcribe(self, audio_path: str, model_name: str = "base", 
                  language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio using the specified model
        
        Args:
            audio_path: Path to audio file
            model_name: Name of the model to use
            language: Language code (optional)
            
        Returns:
            Dictionary with transcription result
        """
        logger.info(f"Transcribing audio with model '{model_name}'")
        start_time = time.time()
        
        try:
            # Load model if not already loaded
            model = self._load_model(model_name)
            
            # Prepare transcription options
            options = {}
            if language:
                options["language"] = language
                
            # Transcribe audio
            result = model.transcribe(audio_path, **options)
            
            # Calculate processing time
            process_time = time.time() - start_time
            logger.info(f"Audio transcribed in {process_time:.2f} seconds")
            
            # Add timing information to result
            result["processing_time"] = process_time
            
            return result
            
        except Exception as e:
            logger.exception(f"Error transcribing audio: {str(e)}")
            raise
    
    def transcribe_chunk(self, audio_path: str, model_name: str = "base",
                        language: Optional[str] = None, is_chunk: bool = True) -> Dict[str, Any]:
        """
        Transcribe a chunk of audio (optimized for streaming)
        
        Args:
            audio_path: Path to audio file
            model_name: Name of the model to use
            language: Language code (optional)
            is_chunk: Whether this is a chunk of a larger audio stream
            
        Returns:
            Dictionary with transcription result
        """
        try:
            # Load model if not already loaded
            model = self._load_model(model_name)
            
            # Prepare transcription options for streaming
            options = {
                "fp16": False,  # Use fp32 for better accuracy with short chunks
                "beam_size": 1  # Faster processing
            }
            
            if language:
                options["language"] = language
                
            # Transcribe audio chunk
            result = model.transcribe(audio_path, **options)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error transcribing audio chunk: {str(e)}")
            raise
    
    def release_memory(self):
        """Release memory by clearing model cache"""
        for model_name in list(self.models.keys()):
            del self.models[model_name]
        
        self.models = {}
        
        # Force garbage collection
        import gc
        gc.collect()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        logger.info("Released model memory") 