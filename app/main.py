from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="Voice Data Collection Platform",
    description="Crowdsourcing platform for Bangla voice recordings and transcriptions",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Voice Data Collection Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}