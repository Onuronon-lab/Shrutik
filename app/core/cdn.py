"""
CDN Integration and Static Asset Optimization

This module provides CDN integration for audio file delivery and static asset optimization.
Supports multiple CDN providers and implements caching strategies for media files.
"""

import hashlib
import logging
import mimetypes
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from app.core.cache import cache_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class CDNConfig:
    """CDN configuration settings."""

    # CDN settings (can be configured via environment variables)
    CDN_ENABLED = os.getenv("CDN_ENABLED", "false").lower() == "true"
    CDN_BASE_URL = os.getenv("CDN_BASE_URL", "")
    CDN_PROVIDER = os.getenv(
        "CDN_PROVIDER", "cloudflare"
    )  # cloudflare, aws, azure, etc.

    # Cache settings
    AUDIO_CACHE_TTL = 86400 * 7  # 7 days for audio files
    STATIC_CACHE_TTL = 86400 * 30  # 30 days for static assets

    # File type configurations
    AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".webm", ".ogg"}
    STATIC_EXTENSIONS = {".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"}

    # Compression settings
    COMPRESS_AUDIO = True
    COMPRESS_STATIC = True

    @classmethod
    def is_cdn_enabled(cls) -> bool:
        """Check if CDN is enabled and properly configured."""
        return cls.CDN_ENABLED and bool(cls.CDN_BASE_URL)


class CDNManager:
    """Manager for CDN operations and URL generation."""

    def __init__(self):
        self.config = CDNConfig()
        self.cache_ttl = 3600  # 1 hour for URL cache

    def get_cdn_url(self, file_path: str, file_type: str = "audio") -> str:
        """
        Generate CDN URL for a file.

        Args:
            file_path: Local file path
            file_type: Type of file (audio, static, etc.)

        Returns:
            CDN URL or local URL if CDN is disabled
        """
        if not self.config.is_cdn_enabled():
            return self._get_local_url(file_path)

        try:
            # Generate cache key for URL
            cache_key = f"cdn_url:{hashlib.md5(file_path.encode()).hexdigest()}"

            # Check cache first
            cached_url = cache_manager.get(cache_key)
            if cached_url:
                return cached_url

            # Generate CDN URL
            cdn_url = self._build_cdn_url(file_path, file_type)

            # Cache the URL
            cache_manager.set(cache_key, cdn_url, self.cache_ttl)

            return cdn_url

        except Exception as e:
            logger.error(f"Error generating CDN URL for {file_path}: {e}")
            return self._get_local_url(file_path)

    def _build_cdn_url(self, file_path: str, file_type: str) -> str:
        """Build CDN URL based on provider and file type."""
        # Normalize file path
        normalized_path = file_path.lstrip("/")

        # Add file type prefix if needed
        if file_type == "audio":
            normalized_path = f"audio/{normalized_path}"
        elif file_type == "static":
            normalized_path = f"static/{normalized_path}"

        # Build full CDN URL
        cdn_url = urljoin(self.config.CDN_BASE_URL.rstrip("/") + "/", normalized_path)

        # Add cache busting parameter for static files
        if file_type == "static":
            file_hash = self._get_file_hash(file_path)
            if file_hash:
                separator = "&" if "?" in cdn_url else "?"
                cdn_url = f"{cdn_url}{separator}v={file_hash[:8]}"

        return cdn_url

    def _get_local_url(self, file_path: str) -> str:
        """Generate local URL for file serving."""
        # Remove uploads prefix if present
        if file_path.startswith("uploads/"):
            file_path = file_path[8:]

        return f"/api/files/{file_path}"

    def _get_file_hash(self, file_path: str) -> Optional[str]:
        """Get file hash for cache busting."""
        try:
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not generate hash for {file_path}: {e}")
        return None

    def get_audio_url(self, chunk_file_path: str) -> str:
        """Get optimized URL for audio chunk."""
        return self.get_cdn_url(chunk_file_path, "audio")

    def get_static_url(self, static_file_path: str) -> str:
        """Get optimized URL for static asset."""
        return self.get_cdn_url(static_file_path, "static")

    def preload_audio_urls(self, chunk_ids: List[int]) -> Dict[int, str]:
        """Preload CDN URLs for multiple audio chunks."""
        from app.db.database import SessionLocal
        from app.models.audio_chunk import AudioChunk

        urls = {}

        try:
            with SessionLocal() as db:
                chunks = db.query(AudioChunk).filter(AudioChunk.id.in_(chunk_ids)).all()

                for chunk in chunks:
                    urls[chunk.id] = self.get_audio_url(chunk.file_path)

            return urls

        except Exception as e:
            logger.error(f"Error preloading audio URLs: {e}")
            return {}

    def invalidate_cdn_cache(self, file_path: str) -> bool:
        """Invalidate CDN cache for a specific file."""
        try:
            # Remove from local cache
            cache_key = f"cdn_url:{hashlib.md5(file_path.encode()).hexdigest()}"
            cache_manager.delete(cache_key)

            # TODO: Implement CDN-specific cache invalidation
            # This would depend on the CDN provider (CloudFlare, AWS CloudFront, etc.)

            logger.info(f"Invalidated CDN cache for {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error invalidating CDN cache for {file_path}: {e}")
            return False


class StaticAssetOptimizer:
    """Optimizer for static assets and media files."""

    def __init__(self, cdn_manager: CDNManager = None):
        self.cdn_manager = cdn_manager or CDNManager()
        self.config = CDNConfig()

    def optimize_audio_delivery(
        self, file_path: str, user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Optimize audio file delivery based on client capabilities.

        Args:
            file_path: Path to audio file
            user_agent: Client user agent string

        Returns:
            Optimization configuration
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

            optimization = {
                "url": self.cdn_manager.get_audio_url(file_path),
                "original_format": file_ext,
                "file_size": file_size,
                "cache_headers": self._get_cache_headers("audio"),
                "compression": self._should_compress_audio(file_ext, file_size),
                "streaming": self._should_enable_streaming(file_size),
                "preload": self._should_preload(file_size),
            }

            # Add format alternatives if available
            optimization["alternatives"] = self._get_format_alternatives(file_path)

            return optimization

        except Exception as e:
            logger.error(f"Error optimizing audio delivery for {file_path}: {e}")
            return {"url": self.cdn_manager.get_audio_url(file_path), "error": str(e)}

    def _get_cache_headers(self, file_type: str) -> Dict[str, str]:
        """Generate appropriate cache headers for file type."""
        if file_type == "audio":
            max_age = self.config.AUDIO_CACHE_TTL
        else:
            max_age = self.config.STATIC_CACHE_TTL

        return {
            "Cache-Control": f"public, max-age={max_age}, immutable",
            "Expires": (datetime.utcnow() + timedelta(seconds=max_age)).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            ),
            "ETag": f'"{hashlib.md5(file_type.encode()).hexdigest()[:16]}"',
        }

    def _should_compress_audio(self, file_ext: str, file_size: int) -> bool:
        """Determine if audio file should be compressed."""
        # Don't compress already compressed formats
        compressed_formats = {".mp3", ".m4a", ".ogg"}
        if file_ext in compressed_formats:
            return False

        # Compress large uncompressed files
        return file_size > 1024 * 1024  # 1MB threshold

    def _should_enable_streaming(self, file_size: int) -> bool:
        """Determine if streaming should be enabled for file."""
        # Enable streaming for files larger than 5MB
        return file_size > 5 * 1024 * 1024

    def _should_preload(self, file_size: int) -> bool:
        """Determine if file should be preloaded."""
        # Preload small files (< 1MB)
        return file_size < 1024 * 1024

    def _get_format_alternatives(self, file_path: str) -> List[Dict[str, str]]:
        """Get alternative formats for the file if available."""
        alternatives = []
        base_path = os.path.splitext(file_path)[0]

        # Check for common alternative formats
        alt_formats = [".mp3", ".ogg", ".m4a"]

        for fmt in alt_formats:
            alt_path = f"{base_path}{fmt}"
            if os.path.exists(alt_path):
                alternatives.append(
                    {
                        "format": fmt,
                        "url": self.cdn_manager.get_audio_url(alt_path),
                        "mime_type": mimetypes.guess_type(alt_path)[0] or "audio/mpeg",
                    }
                )

        return alternatives


class MediaDeliveryService:
    """Service for optimized media file delivery."""

    def __init__(self):
        self.cdn_manager = CDNManager()
        self.optimizer = StaticAssetOptimizer(self.cdn_manager)

    def get_optimized_audio_response(
        self, chunk_id: int, user_agent: str = None
    ) -> Dict[str, Any]:
        """Get optimized audio response for a chunk."""
        try:
            from app.db.database import SessionLocal
            from app.models.audio_chunk import AudioChunk

            with SessionLocal() as db:
                chunk = db.query(AudioChunk).filter(AudioChunk.id == chunk_id).first()

                if not chunk:
                    return {"error": "Chunk not found"}

                # Get optimization configuration
                optimization = self.optimizer.optimize_audio_delivery(
                    chunk.file_path, user_agent
                )

                # Add chunk metadata
                optimization.update(
                    {
                        "chunk_id": chunk.id,
                        "duration": chunk.duration,
                        "start_time": chunk.start_time,
                        "end_time": chunk.end_time,
                    }
                )

                return optimization

        except Exception as e:
            logger.error(
                f"Error getting optimized audio response for chunk {chunk_id}: {e}"
            )
            return {"error": str(e)}

    def batch_optimize_audio_urls(
        self, chunk_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """Batch optimize audio URLs for multiple chunks."""
        try:
            # Preload CDN URLs
            urls = self.cdn_manager.preload_audio_urls(chunk_ids)

            # Get optimization configs
            optimizations = {}
            for chunk_id in chunk_ids:
                if chunk_id in urls:
                    optimizations[chunk_id] = {
                        "url": urls[chunk_id],
                        "cache_headers": self.optimizer._get_cache_headers("audio"),
                        "preload": True,
                    }

            return optimizations

        except Exception as e:
            logger.error(f"Error batch optimizing audio URLs: {e}")
            return {}


# Global instances
cdn_manager = CDNManager()
static_optimizer = StaticAssetOptimizer(cdn_manager)
media_delivery = MediaDeliveryService()
