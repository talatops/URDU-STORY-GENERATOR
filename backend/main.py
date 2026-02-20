"""
FastAPI backend service for Urdu story generation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import sys
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tokenizer.loader import load_tokenizer
from model.kneser_ney_ngram import KneserNeyNGramModel


app = FastAPI(title="Urdu Story Generation API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model and tokenizer (loaded at startup)
tokenizer = None
model: Optional[KneserNeyNGramModel] = None


class GenerateRequest(BaseModel):
    prefix: str
    max_length: int = 500
    temperature: float = 1.0


class GenerateResponse(BaseModel):
    story: str
    tokens_generated: int


def load_models():
    """Load tokenizer and model."""
    global tokenizer, model
    
    tokenizer_path = "models/tokenizer.json"
    # Prefer new Kneser–Ney 4‑gram model; fall back to old trigram if needed
    kn_model_path = "models/kneser_ney_4gram.json"
    old_trigram_path = "models/trigram.json"
    
    if not os.path.exists(tokenizer_path):
        raise FileNotFoundError(f"Tokenizer not found at {tokenizer_path}")
    if not os.path.exists(kn_model_path) and not os.path.exists(old_trigram_path):
        raise FileNotFoundError(
            f"No language model found. Expected {kn_model_path} or {old_trigram_path}"
        )
    
    print("Loading tokenizer...")
    tokenizer = load_tokenizer(tokenizer_path)
    
    # Load Kneser–Ney 4‑gram model if available
    if os.path.exists(kn_model_path):
        print("Loading Kneser–Ney 4‑gram model...")
        model = KneserNeyNGramModel()
        model.load(kn_model_path)
    else:
        # Backward‑compatibility: load old trigram model if present
        from model.trigram import TrigramModel  # type: ignore

        print("Loading legacy trigram model (fallback)...")
        legacy_model = TrigramModel()
        legacy_model.load(old_trigram_path)
        # Wrap legacy model in a thin adapter so downstream code can use .generate()
        model = legacy_model  # type: ignore
    
    print("Models loaded successfully!")


@app.on_event("startup")
async def startup_event():
    """Load models in background so app can respond to healthchecks immediately."""
    import asyncio

    def _load():
        try:
            load_models()
        except Exception as e:
            print(f"Error loading models: {e}")
            print("Models will be loaded lazily on first request.")

    asyncio.get_event_loop().run_in_executor(None, _load)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Urdu Story Generation API",
        "models_loaded": tokenizer is not None and model is not None
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_story(request: GenerateRequest):
    """
    Generate Urdu story from prefix.
    
    Args:
        request: GenerateRequest with prefix, max_length, and temperature
        
    Returns:
        Generated story text
    """
    # Lazy load models if not loaded
    global tokenizer, model
    if tokenizer is None or model is None:
        try:
            load_models()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading models: {str(e)}")
    
    try:
        # Encode prefix
        prefix_tokens = tokenizer.encode(request.prefix)
        
        if len(prefix_tokens) == 0:
            raise HTTPException(status_code=400, detail="Prefix could not be tokenized")
        
        # Generate story
        generated_tokens = model.generate(
            prefix_tokens,
            max_length=request.max_length,
            temperature=request.temperature
        )
        
        # Decode to text
        story = tokenizer.decode(generated_tokens)
        
        # Count generated tokens (excluding prefix)
        tokens_generated = len(generated_tokens) - len(prefix_tokens)
        
        return GenerateResponse(
            story=story,
            tokens_generated=tokens_generated
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@app.get("/generate/stream")
async def generate_story_stream(prefix: str, max_length: int = 500, temperature: float = 1.0):
    """
    Generate Urdu story with streaming response (Server-Sent Events).
    
    Args:
        prefix: Starting phrase in Urdu
        max_length: Maximum generation length
        temperature: Sampling temperature
        
    Returns:
        StreamingResponse with SSE events
    """
    # Lazy load models if not loaded
    global tokenizer, model
    if tokenizer is None or model is None:
        try:
            load_models()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading models: {str(e)}")
    
    def generate():
        try:
            # Encode prefix
            prefix_tokens = tokenizer.encode(prefix)
            
            if len(prefix_tokens) == 0:
                yield f"data: {json.dumps({'error': 'Prefix could not be tokenized'})}\n\n"
                return
            
            # Start with prefix
            generated_tokens = prefix_tokens.copy()
            eot_token = 2  # <EOT> token ID

            # Generate tokens one by one using model's next‑token API.
            # For Kneser–Ney 4‑gram, this will look at up to the last 3 tokens.
            while len(generated_tokens) < max_length:
                history = generated_tokens[-3:] if len(generated_tokens) >= 1 else []

                # Some older models may not implement the new signature; fall back if needed.
                if hasattr(model, "generate_next_token"):
                    try:
                        next_token = model.generate_next_token(history, temperature=temperature)
                    except TypeError:
                        # Legacy trigram signature generate_next_token(w1, w2, temperature)
                        if len(generated_tokens) < 2:
                            w1, w2 = 0, generated_tokens[0] if generated_tokens else 0
                        else:
                            w1, w2 = generated_tokens[-2], generated_tokens[-1]
                        next_token = model.generate_next_token(w1, w2, temperature=temperature)  # type: ignore
                else:
                    # As a last resort, regenerate the whole sequence up to next length
                    next_tokens = model.generate(generated_tokens, max_length=len(generated_tokens) + 1, temperature=temperature)
                    next_token = next_tokens[-1]

                generated_tokens.append(next_token)

                # Decode current state
                current_text = tokenizer.decode(generated_tokens)

                # Send update
                yield f"data: {json.dumps({'text': current_text, 'token': next_token})}\n\n"

                # Stop if EOT token
                if next_token == eot_token:
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    break

            # Final message
            yield f"data: {json.dumps({'done': True, 'final': tokenizer.decode(generated_tokens)})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
