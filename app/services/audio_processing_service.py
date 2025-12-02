"""
Audio Processing Service for intelligent audio chunking.

This service integrates existing CLI audio processing components and provides
intelligent chunking using librosa for VAD and sentence boundary detection.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AudioProcessingError, ErrorContext
from app.core.logging_config import get_logger
from app.models.audio_chunk import AudioChunk
from app.models.voice_recording import RecordingStatus, VoiceRecording

logger = get_logger(__name__)


class AudioChunkingService:
    """Service for intelligent audio chunking using VAD and sentence boundary detection."""

    def __init__(self):
        self.chunk_min_duration = settings.CHUNK_MIN_DURATION
        self.chunk_max_duration = settings.CHUNK_MAX_DURATION
        self.sample_rate = 22050  # Standard sample rate for librosa

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return audio data and sample rate."""
        with ErrorContext(
            "audio loading", AudioProcessingError, logger, file_path=file_path
        ):
            # Validate file exists and is readable
            if not os.path.exists(file_path):
                raise AudioProcessingError(f"Audio file not found: {file_path}")

            if not os.access(file_path, os.R_OK):
                raise AudioProcessingError(f"Audio file not readable: {file_path}")

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise AudioProcessingError(f"Audio file is empty: {file_path}")

            logger.info(f"Loading audio file: {file_path} ({file_size} bytes)")

            # Try loading with librosa first (handles most formats)
            try:
                audio_data, sr = librosa.load(file_path, sr=self.sample_rate)
                logger.info(
                    f"Successfully loaded with librosa: duration={len(audio_data)/sr:.2f}s, sr={sr}"
                )
                return audio_data, sr
            except Exception as e:
                logger.warning(f"librosa failed to load {file_path}, trying pydub: {e}")

                # Fallback to pydub for more format support
                try:
                    audio_segment = AudioSegment.from_file(file_path)
                    audio_data = np.array(
                        audio_segment.get_array_of_samples(), dtype=np.float32
                    )

                    # Convert to mono if stereo
                    if audio_segment.channels == 2:
                        audio_data = audio_data.reshape((-1, 2)).mean(axis=1)
                        logger.info("Converted stereo audio to mono")

                    # Normalize to [-1, 1] range
                    audio_data = audio_data / (2**15)  # Assuming 16-bit audio

                    # Resample if needed
                    if audio_segment.frame_rate != self.sample_rate:
                        logger.info(
                            f"Resampling from {audio_segment.frame_rate}Hz to {self.sample_rate}Hz"
                        )
                        audio_data = librosa.resample(
                            audio_data,
                            orig_sr=audio_segment.frame_rate,
                            target_sr=self.sample_rate,
                        )

                    logger.info(
                        f"Successfully loaded with pydub: duration={len(audio_data)/self.sample_rate:.2f}s"
                    )
                    return audio_data, self.sample_rate

                except Exception as fallback_error:
                    raise AudioProcessingError(
                        f"Failed to load audio file with both librosa and pydub",
                        details={
                            "file_path": file_path,
                            "file_size": file_size,
                            "librosa_error": str(e),
                            "pydub_error": str(fallback_error),
                        },
                    )

    def detect_voice_activity(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """
        Detect voice activity using energy-based VAD.
        Returns boolean array indicating voice activity.
        """
        with ErrorContext("voice activity detection", AudioProcessingError, logger):
            if len(audio_data) == 0:
                raise AudioProcessingError(
                    "Cannot detect voice activity on empty audio data"
                )

            # Frame-based energy calculation
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)  # 10ms hop

            logger.debug(
                f"VAD parameters: frame_length={frame_length}, hop_length={hop_length}"
            )

            # Calculate RMS energy for each frame
            rms_energy = librosa.feature.rms(
                y=audio_data, frame_length=frame_length, hop_length=hop_length
            )[0]

            if len(rms_energy) == 0:
                raise AudioProcessingError("No energy frames calculated for VAD")

            # Dynamic threshold based on audio statistics
            energy_threshold = np.percentile(
                rms_energy, 30
            )  # 30th percentile as threshold
            logger.debug(f"VAD energy threshold: {energy_threshold}")

            # Voice activity detection
            voice_activity = rms_energy > energy_threshold

            # Apply median filter to smooth VAD decisions
            try:
                from scipy.signal import medfilt

                voice_activity = medfilt(
                    voice_activity.astype(int), kernel_size=5
                ).astype(bool)
            except ImportError:
                logger.warning("scipy not available, skipping VAD smoothing")

            logger.debug(
                f"VAD detected {np.sum(voice_activity)} voice frames out of {len(voice_activity)}"
            )
            return voice_activity

    def find_sentence_boundaries(self, audio_data: np.ndarray, sr: int) -> List[float]:
        """
        Find sentence boundaries using silence detection and spectral features.
        Returns list of boundary timestamps in seconds.
        """
        # Detect voice activity
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)  # 10ms hop

        voice_activity = self.detect_voice_activity(audio_data, sr)

        # Convert frame indices to time
        frame_times = librosa.frames_to_time(
            np.arange(len(voice_activity)), sr=sr, hop_length=hop_length
        )

        # Find silence regions (gaps in voice activity)
        silence_regions = []
        in_silence = False
        silence_start = 0

        for i, is_voice in enumerate(voice_activity):
            if not is_voice and not in_silence:
                # Start of silence
                silence_start = frame_times[i]
                in_silence = True
            elif is_voice and in_silence:
                # End of silence
                silence_end = frame_times[i]
                silence_duration = silence_end - silence_start

                # Only consider significant silences (>200ms) as potential boundaries
                if silence_duration > 0.2:
                    silence_regions.append(
                        (silence_start, silence_end, silence_duration)
                    )

                in_silence = False

        # Extract boundary points (middle of silence regions)
        boundaries = []
        for start, end, duration in silence_regions:
            # Prefer longer silences as sentence boundaries
            if duration > 0.5:  # Strong boundary for silences > 500ms
                boundaries.append((start + end) / 2)
            elif duration > 0.3:  # Weak boundary for silences > 300ms
                boundaries.append((start + end) / 2)

        return sorted(boundaries)

    def create_chunks_intelligent(
        self, audio_data: np.ndarray, sr: int, sentence_boundaries: List[float]
    ) -> List[Tuple[float, float]]:
        """
        Create audio chunks based on sentence boundaries with duration constraints.
        Returns list of (start_time, end_time) tuples.
        """
        audio_duration = len(audio_data) / sr
        chunks = []

        if not sentence_boundaries:
            # Fallback to time-based chunking if no boundaries found
            return self.create_chunks_time_based(audio_duration)

        # Add start and end boundaries
        all_boundaries = [0.0] + sentence_boundaries + [audio_duration]
        all_boundaries = sorted(set(all_boundaries))  # Remove duplicates and sort

        current_start = 0.0
        i = 1

        while i < len(all_boundaries) and current_start < audio_duration:
            potential_end = all_boundaries[i]
            chunk_duration = potential_end - current_start

            # If chunk is within acceptable duration, use it
            if self.chunk_min_duration <= chunk_duration <= self.chunk_max_duration:
                chunks.append((current_start, potential_end))
                current_start = potential_end
                i += 1

            # If chunk is too short, try to extend to next boundary
            elif chunk_duration < self.chunk_min_duration:
                # Look ahead for a better boundary
                extended_end = potential_end
                for j in range(i + 1, len(all_boundaries)):
                    test_end = all_boundaries[j]
                    test_duration = test_end - current_start

                    if test_duration <= self.chunk_max_duration:
                        extended_end = test_end
                        i = j  # Update index to skip processed boundaries
                    else:
                        break

                # If still too short, use time-based extension
                final_duration = extended_end - current_start
                if final_duration < self.chunk_min_duration:
                    extended_end = min(
                        current_start + self.chunk_min_duration, audio_duration
                    )

                chunks.append((current_start, extended_end))
                current_start = extended_end
                i += 1

            # If chunk is too long, split it
            else:
                # Split into smaller chunks while respecting boundaries
                temp_start = current_start
                while temp_start < potential_end:
                    temp_end = min(temp_start + self.chunk_max_duration, potential_end)

                    # Try to find a nearby boundary for a cleaner cut
                    for boundary in sentence_boundaries:
                        if (
                            temp_start < boundary < temp_end
                            and (temp_end - boundary) > 0.5
                        ):
                            temp_end = boundary
                            break

                    if temp_end > temp_start:  # Ensure valid chunk
                        chunks.append((temp_start, temp_end))
                    temp_start = temp_end

                current_start = potential_end
                i += 1

        # Handle any remaining audio
        if current_start < audio_duration:
            remaining_duration = audio_duration - current_start
            if remaining_duration >= self.chunk_min_duration:
                chunks.append((current_start, audio_duration))

        # Filter out invalid chunks
        valid_chunks = []
        for start, end in chunks:
            if start < end and (end - start) >= 0.1:  # At least 100ms
                valid_chunks.append((start, end))

        return valid_chunks

    def create_chunks_time_based(
        self, audio_duration: float
    ) -> List[Tuple[float, float]]:
        """
        Fallback method: create chunks based on fixed time intervals.
        Returns list of (start_time, end_time) tuples.
        """
        chunks = []
        chunk_duration = min(
            self.chunk_max_duration, max(self.chunk_min_duration, 5.0)
        )  # Default 5s

        current_time = 0.0
        while current_time < audio_duration:
            end_time = min(current_time + chunk_duration, audio_duration)
            chunks.append((current_time, end_time))
            current_time = end_time

        return chunks

    def save_chunk(
        self,
        audio_data: np.ndarray,
        sr: int,
        start_time: float,
        end_time: float,
        output_path: str,
    ) -> Dict[str, Any]:
        """
        Save audio chunk to file and return metadata.
        """
        try:
            # Extract chunk from audio data
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            chunk_data = audio_data[start_sample:end_sample]

            # Check for empty chunk
            if len(chunk_data) == 0:
                raise AudioProcessingError(
                    f"Empty chunk: start={start_time}, end={end_time}"
                )

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Save chunk as WAV file
            sf.write(output_path, chunk_data, sr)

            # Calculate metadata
            duration = end_time - start_time
            rms_energy = np.sqrt(np.mean(chunk_data**2)) if len(chunk_data) > 0 else 0.0
            max_amplitude = np.max(np.abs(chunk_data)) if len(chunk_data) > 0 else 0.0

            metadata = {
                "duration": duration,
                "sample_rate": sr,
                "rms_energy": float(rms_energy),
                "max_amplitude": float(max_amplitude),
                "samples": len(chunk_data),
                "file_size": os.path.getsize(output_path),
            }

            return metadata

        except Exception as e:
            raise AudioProcessingError(f"Failed to save chunk {output_path}: {e}")

    def process_recording(
        self, recording_id: int, file_path: str, db: Session
    ) -> List[AudioChunk]:
        """
        Main method to process a recording and create chunks.
        Returns list of created AudioChunk objects.
        """
        try:
            logger.info(f"Starting audio processing for recording {recording_id}")

            # Update recording status
            recording = (
                db.query(VoiceRecording)
                .filter(VoiceRecording.id == recording_id)
                .first()
            )

            if not recording:
                raise AudioProcessingError(f"Recording {recording_id} not found")

            recording.status = RecordingStatus.PROCESSING
            db.commit()

            # Load audio
            audio_data, sr = self.load_audio(file_path)
            audio_duration = len(audio_data) / sr

            logger.info(f"Loaded audio: duration={audio_duration:.2f}s, sr={sr}")

            # Find sentence boundaries using intelligent detection
            try:
                sentence_boundaries = self.find_sentence_boundaries(audio_data, sr)
                logger.info(f"Found {len(sentence_boundaries)} sentence boundaries")

                # Create chunks based on boundaries
                chunk_intervals = self.create_chunks_intelligent(
                    audio_data, sr, sentence_boundaries
                )

            except Exception as e:
                logger.warning(
                    f"Intelligent chunking failed: {e}, falling back to time-based"
                )
                chunk_intervals = self.create_chunks_time_based(audio_duration)

            logger.info(f"Created {len(chunk_intervals)} chunks")

            # Create chunk directory
            chunks_dir = Path(settings.UPLOAD_DIR) / "chunks" / str(recording_id)
            chunks_dir.mkdir(parents=True, exist_ok=True)

            # Process each chunk and prepare for bulk insert
            audio_chunks = []
            for i, (start_time, end_time) in enumerate(chunk_intervals):
                # Skip empty or invalid chunks
                if start_time >= end_time or (end_time - start_time) < 0.1:
                    logger.warning(
                        f"Skipping invalid chunk {i}: {start_time}s - {end_time}s"
                    )
                    continue

                chunk_filename = f"chunk_{i:03d}.wav"
                chunk_path = chunks_dir / chunk_filename

                try:
                    # Save chunk file
                    chunk_metadata = self.save_chunk(
                        audio_data, sr, start_time, end_time, str(chunk_path)
                    )

                    # Create database record with export optimization fields initialized
                    audio_chunk = AudioChunk(
                        recording_id=recording_id,
                        chunk_index=i,
                        file_path=str(chunk_path),
                        start_time=float(start_time),
                        end_time=float(end_time),
                        duration=float(end_time - start_time),
                        meta_data=chunk_metadata,
                        transcript_count=0,
                        ready_for_export=False,
                        consensus_quality=0.0,
                        consensus_failed_count=0,
                    )

                    audio_chunks.append(audio_chunk)

                except AudioProcessingError as e:
                    logger.warning(f"Failed to save chunk {i}: {e}")
                    continue

            # Bulk insert all chunks in a single transaction
            if audio_chunks:
                db.bulk_save_objects(audio_chunks)
                logger.info(
                    f"Bulk inserted {len(audio_chunks)} chunks for recording {recording_id}"
                )

            # Update recording status
            recording.status = RecordingStatus.CHUNKED
            db.commit()

            logger.info(
                f"Successfully processed recording {recording_id} into {len(audio_chunks)} chunks"
            )
            return audio_chunks

        except Exception as e:
            logger.error(f"Failed to process recording {recording_id}: {e}")

            # Update recording status to failed
            if recording:
                recording.status = RecordingStatus.FAILED
                db.commit()

            raise AudioProcessingError(f"Audio processing failed: {e}")


# Global service instance
audio_chunking_service = AudioChunkingService()
