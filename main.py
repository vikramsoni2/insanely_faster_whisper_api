from contextlib import asynccontextmanager    
from fastapi import FastAPI, File, UploadFile, Query, Request, Response, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import torch, torchaudio, io
from transformers import pipeline
from transformers.utils import is_flash_attn_2_available
import traceback
from tempfile import NamedTemporaryFile
import json
import uvicorn
import os


description = """
Whisper Transcription API is using OpenAI Whisper model, which is an automatic speech recognition (ASR) system, uses two-letter ISO 639-1 language codes to specify languages. 

Whisper's performance varies widely depending on the language. The figure below shows a performance breakdown of large-v3 and large-v2 models by language, using WERs (word error rates) or CER (character error rates, shown in Italic) evaluated on the Common Voice 15 and Fleurs datasets. 

![Your Image](https://github.com/openai/whisper/assets/266841/f4619d66-1058-4005-8f67-a9d811b77c62)
"""

origins = [
    "*"
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model

    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    app.whisper_pipeline = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-large-v3", # select checkpoint from https://huggingface.co/openai/whisper-large-v3#model-details
        torch_dtype=torch.float16 if device.startswith("cuda") else torch.float32,
        device=device,
        model_kwargs={"attn_implementation": "flash_attention_2"} if is_flash_attn_2_available() else {"attn_implementation": "sdpa"},
    )
    
    # await init_db()

    yield
    # Clean up the ML models and release the resources
    app.whisper_pipeline = None


app = FastAPI(lifespan=lifespan,
              title="Whisper Transcription API", 
              description=description, 
              version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join("static", "index.html"))


@app.get("/health")
def healthcheck():
    """
    Health Check Endpoint
    This endpoint is used to check the health of the API.
    It returns a status message indicating if the API is operational.
    """
    return {"status":"ok"}


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(..., description="Audio file for transcription. In WAV, MP3, AAC, or OGG format"), 
    language: str = Form("EN", pattern="^(?:[A-Za-z]{2}|auto)$", description="Two-letter ISO 639-1 language code or 'auto' for automatic detection."),
    timestamp: bool = Form(False, description="Whether to include timestamps in the transcription."),
):
    """
    Transcribe Audio Endpoint
    Accepts an audio file and transcribes it to text using the OpenAI Whisper model.
    
    Args:
    - file: An audio file in .AAC, .FLAC, .MP3, .OGG, .WAV, or .WMA format.
    - language: A two-letter ISO 639-1 code of the language in the audio, or 'auto' for automatic detection of language.
    - timestamp: Flag to determine if timestamps should be included in the transcription.
    
    Returns:
    A JSON response containing the transcribed text.
    """

    
    extra_args = {
        "chunk_length_s": 30, 
        "batch_size": 24, 
        "return_timestamps": timestamp}
    
    if(language !="auto"):
        extra_args["generate_kwargs"] = {
            "task":"transcribe",
            "language": f"<|{language.lower()}|>"
        }
    
    try:
        with NamedTemporaryFile(suffix=f".{file.filename.split('.')[-1]}") as tmp:
            tmp.write(await file.read())
            tmp.flush()
            tmp.seek(0)
            outputs = app.whisper_pipeline(tmp.name, **extra_args)
            
        return outputs
    
    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)