from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import AuthContextMiddleware
from app.api.auth import router as auth_router

app = FastAPI(
    title="Voice Data Collection Platform",
    description="Crowdsourcing platform for Bangla voice recordings and transcriptions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthContextMiddleware)

app.include_router(auth_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Voice Data Collection Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}