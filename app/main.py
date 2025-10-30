from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import AuthContextMiddleware
from app.api.auth import router as auth_router
from app.api.scripts import router as scripts_router
from app.api.voice_recordings import router as voice_recordings_router
from app.api.transcriptions import router as transcriptions_router
from app.api.consensus import router as consensus_router
from app.api.admin import router as admin_router
from app.api.export import router as export_router

app = FastAPI(
    title="Voice Data Collection Platform",
    description="Crowdsourcing platform for Bangla voice recordings and transcriptions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(AuthContextMiddleware)

app.include_router(auth_router, prefix="/api")
app.include_router(scripts_router, prefix="/api")
app.include_router(voice_recordings_router, prefix="/api")
app.include_router(transcriptions_router, prefix="/api")
app.include_router(consensus_router)
app.include_router(admin_router, prefix="/api")
app.include_router(export_router)

@app.get("/")
async def root():
    return {"message": "Voice Data Collection Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}