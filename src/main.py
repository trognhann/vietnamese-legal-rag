from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Vietnamese Legal RAG API",
    description="Backend API for querying the Vietnamese Legal RAG System.",
    version="1.0.0"
)

# Configure CORS so Streamlit UI or other frontends can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Vietnamese Legal RAG API is running."}

# TODO: include routers from src.api
# from src.api.routes import router as api_router
# app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    # Run the application locally on port 8000
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
