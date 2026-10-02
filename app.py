import logging
import os
from pathlib import Path
from typing import Optional
import numpy as np
import librosa
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import torch
from transformers import AutoModelForCTC, AutoProcessor
 
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
# Initialize FastAPI app
app = FastAPI(
    title="Hohe ASR Amharic API",
    description="Automatic Speech Recognition API for Amharic audio",
    version="1.0.0"
)
 
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Global model and processor
model = None
processor = None
device = None
 
class TranscriptionResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    model: str = "snapwre/hohe-asr-amharic"
    language: str = "am"
 
class ErrorResponse(BaseModel):
    error: str
    detail: str
 
@app.on_event("startup")
async def load_model():
    """Load model and processor on startup"""
    global model, processor, device
 
    try:
        logger.info("Loading Hohe ASR Amharic model...")
 
        # Determine device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")
 
        # Set Hugging Face cache directory
        os.environ['HF_HOME'] = os.getenv('HF_HOME', '/tmp/huggingface')
 
        # Load model and processor
        model_name = "snapwre/hohe-asr-amharic"
        processor = AutoProcessor.from_pretrained(model_name)
        model = AutoModelForCTC.from_pretrained(model_name)
        model = model.to(device)
        model.eval()
 
        logger.info("Model loaded successfully!")
        logger.info(f"Model device: {next(model.parameters()).device}")
 
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise
 
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": str(device)
    }
 
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Hohe ASR Amharic API",
        "version": "1.0.0",
        "model": "snapwre/hohe-asr-amharic",
        "language": "Amharic",
        "endpoints": {
            "health": "/health",
            "transcribe": "/transcribe",
            "info": "/info"
        }
    }
 
@app.get("/info")
async def model_info():
    """Get model information"""
    return {
        "model_name": "hohe-asr-amharic",
        "model_id": "snapwre/hohe-asr-amharic",
        "task": "automatic-speech-recognition",
        "language": "Amharic",
        "device": str(device),
        "framework": "PyTorch with Hugging Face Transformers"
    }
 
@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(file: UploadFile = File(...)):
    """
    Transcribe audio file to Amharic text
 
    Supported formats: WAV, MP3, FLAC, OGG
    Max file size: 100MB
    """
 
    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
 
    try:
        # Validate file
        if file.content_type not in ["audio/wav", "audio/mpeg", "audio/flac", "audio/ogg", "application/octet-stream"]:
            raise HTTPException(status_code=400, detail=f"Unsupported audio format: {file.content_type}")
 
        # Read audio file
        logger.info(f"Processing audio file: {file.filename}")
        audio_data = await file.read()
 
        # Load audio with librosa
        audio_array, sampling_rate = librosa.load(
            audio_data,
            sr=16000,  # Resample to 16kHz
            mono=True
        )
 
        logger.info(f"Audio loaded: {len(audio_array)} samples at {sampling_rate}Hz")
 
        # Process audio
        with torch.no_grad():
            inputs = processor(
                audio_array,
                sampling_rate=sampling_rate,
                return_tensors="pt"
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
 
            # Get logits from model
            logits = model(**inputs).logits
 
        # Decode predictions
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.batch_decode(predicted_ids)[0]
 
        logger.info(f"Transcription complete: {transcription}")
 
        return TranscriptionResponse(
            text=transcription,
            confidence=None  # Confidence scoring would require additional processing
        )
 
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
 
@app.post("/transcribe-batch")
async def transcribe_batch(files: list[UploadFile] = File(...)):
    """
    Transcribe multiple audio files
    Returns list of transcriptions
    """
 
    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
 
    results = []
 
    for file in files:
        try:
            audio_data = await file.read()
            audio_array, sampling_rate = librosa.load(
                audio_data,
                sr=16000,
                mono=True
            )
 
            with torch.no_grad():
                inputs = processor(
                    audio_array,
                    sampling_rate=sampling_rate,
                    return_tensors="pt"
                )
                inputs = {k: v.to(device) for k, v in inputs.items()}
                logits = model(**inputs).logits
 
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = processor.batch_decode(predicted_ids)[0]
 
            results.append({
                "filename": file.filename,
                "text": transcription,
                "status": "success"
            })
 
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e),
                "status": "failed"
            })
 
    return {"results": results, "total": len(results)}
 
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
 