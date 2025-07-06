from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create the FastAPI app FIRST
app = FastAPI(title="Joke Battles API", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import after app creation to avoid circular imports
from llm_clients import LLMClients
from database import Database

# Initialize database and LLM clients
db = Database()
llm_clients = LLMClients()

# Initialize database
db.init_db()
logger.info("Database initialized")

# Serve React build files
if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")


# Pydantic models
class JokeRequest(BaseModel):
    context: str
    session_id: str


class VoteRequest(BaseModel):
    model: str
    session_id: str


class JokeResponse(BaseModel):
    id: int
    content: str
    model: str


class ScoreResponse(BaseModel):
    model: str
    votes: int
    icon: str


@app.get("/")
async def root():
    return {"message": "Joke Battles API is running!"}


@app.post("/api/generate-jokes", response_model=List[JokeResponse])
async def generate_jokes(request: JokeRequest):
    """Generate jokes from all 4 AI models"""
    try:
        logger.info(f"Generating jokes for context: {request.context}")

        # Generate jokes from all models concurrently with individual error handling
        import asyncio

        async def safe_generate(func, model_name):
            try:
                result = await func(request.context)
                if result.startswith("Sorry,"):  # It's a fallback message
                    logger.warning(f"{model_name} returned fallback message")
                    return result
                else:
                    logger.info(f"{model_name} joke generated successfully: {result[:30]}...")
                    return result
            except Exception as e:
                logger.error(f"Error generating {model_name} joke: {e}")
                return f"Sorry, {model_name} is taking a joke break right now! 😅"

        tasks = [
            safe_generate(llm_clients.generate_openai_joke, "OpenAI"),
            safe_generate(llm_clients.generate_anthropic_joke, "Anthropic"),
            safe_generate(llm_clients.generate_gemini_joke, "Gemini"),
            safe_generate(llm_clients.generate_llama_joke, "Llama")
        ]

        jokes = await asyncio.gather(*tasks)

        # Format response
        response = []
        models = ['OpenAI', 'Anthropic', 'Gemini', 'Llama']

        for i, (joke, model) in enumerate(zip(jokes, models)):
            response.append(JokeResponse(
                id=i,
                content=joke,
                model=model
            ))

        logger.info(f"Successfully generated {len(response)} jokes")
        return response

    except Exception as e:
        logger.error(f"Critical error in generate_jokes: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate jokes")


@app.post("/api/vote")
async def submit_vote(request: VoteRequest):
    """Submit a vote for a model"""
    try:
        # Check if this session has already voted
        if db.has_voted(request.session_id):
            raise HTTPException(status_code=400, detail="Already voted for this session")

        # Record the vote
        db.record_vote(request.model, request.session_id)
        logger.info(f"Vote recorded: {request.model} for session {request.session_id}")

        return {"message": "Vote recorded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_vote: {e}")
        raise HTTPException(status_code=500, detail="Failed to record vote")


@app.get("/debug/test-joke-generation")
async def debug_joke_generation():
    """Debug endpoint to test joke generation with a simple request"""
    from pydantic import BaseModel

    # Create a simple test request
    test_request = JokeRequest(context="cats", session_id="test123")

    try:
        # Call the same function your frontend calls
        result = await generate_jokes(test_request)

        # Return the raw result so we can see exactly what's being generated
        return {
            "success": True,
            "jokes_count": len(result),
            "jokes": [{"id": j.id, "model": j.model, "content": j.content[:50] + "..."} for j in result],
            "full_response": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/debug/test-llms")
async def test_llm_connections():
    """Test all LLM connections"""
    results = {}

    # Test Llama only first
    try:
        llama_joke = await llm_clients.generate_llama_joke("testing")
        results["llama"] = {"status": "success", "response": llama_joke}
    except Exception as e:
        results["llama"] = {"status": "error", "error": str(e)}

    # Test if API keys are loaded
    results["api_keys"] = {
        "openai": "loaded" if llm_clients.openai_api_key else "missing",
        "anthropic": "loaded" if llm_clients.anthropic_api_key else "missing",
        "google": "loaded" if llm_clients.google_api_key else "missing"
    }

    return results


@app.get("/api/scores", response_model=List[ScoreResponse])
async def get_scores():
    """Get current vote counts for all models"""
    try:
        scores = db.get_scores()

        # Add icons for each model
        model_icons = {
            'OpenAI': '🤖',
            'Anthropic': '🎭',
            'Gemini': '⭐',
            'Llama': '🦙'
        }

        response = []
        for model, votes in scores.items():
            response.append(ScoreResponse(
                model=model,
                votes=votes,
                icon=model_icons.get(model, '🤖')
            ))

        return response

    except Exception as e:
        logger.error(f"Error in get_scores: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scores")


# Serve React app for all non-API routes
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all non-API routes"""
    # Don't serve React for API routes
    if full_path.startswith("api/") or full_path.startswith("debug/"):
        raise HTTPException(status_code=404, detail="API route not found")

    # Serve React index.html for all other routes
    if os.path.exists("frontend/build/index.html"):
        return FileResponse("frontend/build/index.html")
    else:
        return {"message": "React app not built yet. Run: cd frontend && npm run build"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)