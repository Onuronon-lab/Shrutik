"""
Tests for audio processing service and chunking functionality.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import numpy as np
import pytest
import soundfile as sf

from app.services.audio_processing_service import (
    AudioChunkingService,
    AudioProcessingError,
)


class TestAudioChunkingService:
    """Test cases for AudioChunkingService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = AudioChunkingService()

    def create_test_audio(
        self, duration: float = 5.0, sample_rate: int = 22050
    ) -> tuple[np.ndarray, int]:
        """Create test audio data."""
        # Generate a simple sine wave with some silence
        t = np.linspace(0, duration, int(duration * sample_rate))

        # Create audio with speech-like patterns (sine waves with pauses)
        audio = np.zeros_like(t)

        # Add some "speech" segments with silence between them
        segment_duration = 1.0  # 1 second segments
        silence_duration = 0.3  # 300ms silence

        current_time = 0
        frequency = 440  # A4 note

        while current_time < duration:
            # Add speech segment
            start_idx = int(current_time * sample_rate)
            end_idx = int(
                min((current_time + segment_duration), duration) * sample_rate
            )

            if end_idx > start_idx:
                segment_t = t[start_idx:end_idx] - current_time
                audio[start_idx:end_idx] = 0.5 * np.sin(
                    2 * np.pi * frequency * segment_t
                )

            current_time += segment_duration + silence_duration

        return audio, sample_rate

    def test_load_audio_with_numpy_array(self):
        """Test loading audio from a temporary WAV file."""
        # Create test audio
        audio_data, sr = self.create_test_audio(duration=3.0)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sr)
            tmp_path = tmp_file.name

        try:
            # Test loading
            loaded_audio, loaded_sr = self.service.load_audio(tmp_path)

            assert loaded_sr == self.service.sample_rate
            assert len(loaded_audio) > 0
            assert isinstance(loaded_audio, np.ndarray)

        finally:
            os.unlink(tmp_path)

    def test_load_audio_nonexistent_file(self):
        """Test loading audio from nonexistent file raises error."""
        with pytest.raises(AudioProcessingError):
            self.service.load_audio("nonexistent_file.wav")

    def test_detect_voice_activity(self):
        """Test voice activity detection."""
        # Create test audio with clear speech and silence patterns
        audio_data, sr = self.create_test_audio(duration=2.0)

        # Detect voice activity
        voice_activity = self.service.detect_voice_activity(audio_data, sr)

        assert isinstance(voice_activity, np.ndarray)
        assert voice_activity.dtype == bool
        assert len(voice_activity) > 0

        # Should detect some voice activity
        assert np.any(voice_activity)

    def test_find_sentence_boundaries(self):
        """Test sentence boundary detection."""
        # Create test audio with clear segments
        audio_data, sr = self.create_test_audio(duration=3.0)

        # Find boundaries
        boundaries = self.service.find_sentence_boundaries(audio_data, sr)

        assert isinstance(boundaries, list)
        assert all(isinstance(b, float) for b in boundaries)
        assert all(0 <= b <= 3.0 for b in boundaries)  # Within audio duration

        # Boundaries should be sorted
        assert boundaries == sorted(boundaries)

    def test_create_chunks_intelligent(self):
        """Test intelligent chunk creation."""
        audio_data, sr = self.create_test_audio(duration=5.0)
        boundaries = [1.0, 2.5, 4.0]  # Test boundaries

        chunks = self.service.create_chunks_intelligent(audio_data, sr, boundaries)

        assert isinstance(chunks, list)
        assert len(chunks) > 0

        # Check chunk format
        for start, end in chunks:
            assert isinstance(start, float)
            assert isinstance(end, float)
            assert start < end
            assert start >= 0
            assert end <= 5.0

            # Check duration constraints
            duration = end - start
            assert (
                self.service.chunk_min_duration
                <= duration
                <= self.service.chunk_max_duration
            )

    def test_create_chunks_time_based(self):
        """Test time-based chunk creation fallback."""
        duration = 10.0
        chunks = self.service.create_chunks_time_based(duration)

        assert isinstance(chunks, list)
        assert len(chunks) > 0

        # Check chunks cover the entire duration
        assert chunks[0][0] == 0.0
        assert chunks[-1][1] == duration

        # Check no gaps between chunks
        for i in range(len(chunks) - 1):
            assert chunks[i][1] == chunks[i + 1][0]

    def test_save_chunk(self):
        """Test saving audio chunk to file."""
        # Create test audio
        audio_data, sr = self.create_test_audio(duration=3.0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "test_chunk.wav")

            # Save chunk
            metadata = self.service.save_chunk(audio_data, sr, 1.0, 2.0, output_path)

            # Check file was created
            assert os.path.exists(output_path)

            # Check metadata
            assert isinstance(metadata, dict)
            assert "duration" in metadata
            assert "sample_rate" in metadata
            assert "rms_energy" in metadata
            assert "max_amplitude" in metadata
            assert "samples" in metadata
            assert "file_size" in metadata

            # Check duration is approximately correct
            assert abs(metadata["duration"] - 1.0) < 0.1

    def test_process_recording_success(self):
        """Test successful recording processing."""
        # Mock database session and recording
        mock_db = Mock()

        mock_recording = Mock()
        mock_recording.id = 1
        mock_recording.status = "uploaded"
        mock_recording.audio_chunks = []

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_recording
        )

        # Create test audio file
        audio_data, sr = self.create_test_audio(duration=2.0)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sr)
            tmp_path = tmp_file.name

        try:
            # Mock the upload directory
            with patch(
                "app.services.audio_processing_service.settings"
            ) as mock_settings:
                with tempfile.TemporaryDirectory() as tmp_upload_dir:
                    mock_settings.UPLOAD_DIR = tmp_upload_dir

                    # Process recording
                    chunks = self.service.process_recording(1, tmp_path, mock_db)

                    # Verify results
                    assert isinstance(chunks, list)
                    assert len(chunks) > 0

                    # Verify database operations
                    mock_db.commit.assert_called()
                    mock_db.add.assert_called()

        finally:
            os.unlink(tmp_path)

    def test_chunk_duration_constraints(self):
        """Test that chunks respect duration constraints."""
        # Test with very short audio
        short_audio, sr = self.create_test_audio(duration=0.5)
        boundaries = []

        chunks = self.service.create_chunks_intelligent(short_audio, sr, boundaries)

        # Should create at least one chunk meeting minimum duration
        assert len(chunks) >= 1
        for start, end in chunks:
            duration = end - start
            assert (
                duration >= self.service.chunk_min_duration or duration == 0.5
            )  # Allow for short audio

    def test_empty_boundaries_fallback(self):
        """Test fallback to time-based chunking when no boundaries found."""
        audio_data, sr = self.create_test_audio(duration=8.0)
        empty_boundaries = []

        chunks = self.service.create_chunks_intelligent(
            audio_data, sr, empty_boundaries
        )

        # Should still create chunks
        assert len(chunks) > 0

        # Should cover entire duration
        assert chunks[0][0] == 0.0
        assert chunks[-1][1] == 8.0


if __name__ == "__main__":
    pytest.main([__file__])
