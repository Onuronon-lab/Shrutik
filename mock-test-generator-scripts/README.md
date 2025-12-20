# Mock Test Generator Scripts

This directory contains scripts for generating test data and testing the complete voice collection and export workflow.

## Scripts Overview

### 1. Data Generation Scripts

#### `generate_test_data.py`

Generates synthetic voice recordings with TTS (Text-to-Speech).

- Creates motivational scripts using content library
- Synthesizes audio using Edge TTS (preferred) or Google TTS (fallback)
- Stores recordings in database with proper metadata
- Supports Docker-compatible file paths

**Usage:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python generate_test_data.py
```

#### `trigger_audio_processing.py`

Triggers Celery audio processing tasks for uploaded recordings.

- Queues recordings for chunking and processing
- Supports batch processing of multiple recordings
- Provides processing statistics and monitoring

**Usage:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python trigger_audio_processing.py
```

### 2. Transcription Automation Scripts

#### `generate_mock_transcriptions.py`

Creates realistic transcriptions for processed audio chunks.

- Generates 5-8 transcriptions per chunk (required for consensus)
- Creates realistic variations with typos, punctuation differences
- Uses multiple mock users to simulate real transcription workflow
- Calculates quality and confidence scores

**Features:**

- Text variation engine with common typos and errors
- Punctuation and capitalization variations
- Quality scoring based on similarity to original
- Automatic consensus calculation triggering

**Usage:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python generate_mock_transcriptions.py
```

#### `prepare_export_data.py`

Calculates consensus for transcribed chunks and marks them ready for export.

- Processes chunks with ≥5 transcriptions
- Calculates consensus quality scores using similarity algorithms
- Marks chunks as `ready_for_export` when quality ≥90%
- Updates chunk metadata for export optimization

**Consensus Algorithm:**

- Pairwise text similarity calculation
- Individual quality score weighting
- Length consistency analysis
- Combined scoring: 60% similarity + 20% quality + 20% consistency

**Usage:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python prepare_export_data.py
```

### 3. Export Testing Scripts

#### `test_export_workflow.py`

Tests the complete export batch functionality end-to-end.

- Creates export batches with different parameters
- Tests batch download functionality
- Verifies export batch contents and metadata
- Tests download limits and rate limiting

**Test Cases:**

- Small batches (10 chunks)
- Medium batches (25 chunks)
- Large batches (50 chunks)
- Local and R2 storage testing
- Download authentication and limits

**Usage:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python test_export_workflow.py
```

## Complete Workflow

To test the entire voice collection and export pipeline:

### Step 1: Generate Voice Recordings

```bash
# Generate synthetic voice recordings
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python generate_test_data.py
```

### Step 2: Process Audio into Chunks

```bash
# Trigger audio processing (chunking)
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python trigger_audio_processing.py
```

### Step 3: Generate Transcriptions

```bash
# Create mock transcriptions for chunks
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python generate_mock_transcriptions.py
```

### Step 4: Calculate Consensus

```bash
# Calculate consensus and mark chunks ready for export
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python prepare_export_data.py
```

### Step 5: Test Export Functionality

```bash
# Test export batch creation and download
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python test_export_workflow.py
```

## Data Flow

```
Voice Recordings → Audio Chunks → Transcriptions → Consensus → Export Batches
     ↓                ↓              ↓             ↓           ↓
generate_test_data → trigger_audio → generate_mock → prepare_ → test_export
                     _processing     _transcriptions  export_   _workflow
                                                     data
```

## Database Schema

The scripts work with the following key tables:

- `voice_recordings`: Original audio files and metadata
- `audio_chunks`: Processed audio segments ready for transcription
- `transcriptions`: User-generated transcriptions of chunks
- `export_batches`: Packaged chunks ready for download
- `export_downloads`: Download tracking and rate limiting

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for Celery (default: redis://localhost:6379/0)
- `AUDIO_OUTPUT_DIR`: Custom audio output directory (optional)

### Storage Configuration

Export functionality supports both local and R2 (Cloudflare) storage:

**Local Storage:**

- Files stored in `uploads/exports/` directory
- Direct file serving for downloads

**R2 Storage:**

- Files uploaded to Cloudflare R2 bucket
- Signed URLs for secure downloads
- Free tier monitoring and limits

## Quality Metrics

### Transcription Quality

- **Similarity Score**: Text similarity between transcriptions (0-1)
- **Individual Quality**: User-provided quality scores
- **Length Consistency**: Variation in transcription lengths
- **Consensus Threshold**: 90% quality required for export

### Export Readiness

- **Minimum Transcriptions**: 5 transcriptions per chunk
- **Quality Threshold**: 90% consensus quality
- **Validation Status**: Automatic validation for high-quality consensus

## Troubleshooting

### Common Issues

1. **TTS Service Failures**
   - Edge TTS requires internet connection
   - Google TTS fallback for offline testing
   - Check firewall and DNS settings

2. **Celery Task Failures**
   - Ensure Redis is running
   - Check Celery worker status
   - Verify audio file permissions

3. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check PostgreSQL service status
   - Ensure database exists and is accessible

4. **Export Batch Creation Failures**
   - Verify chunks are marked `ready_for_export = true`
   - Check storage configuration
   - Ensure sufficient disk space

### Debugging

Enable verbose logging by setting:

```bash
export PYTHONPATH=/path/to/project
export LOG_LEVEL=DEBUG
```

### Performance Optimization

- Use batch processing for large datasets
- Monitor Redis memory usage for Celery
- Consider chunk size limits for export batches
- Use appropriate compression levels for archives

## Dependencies

Core dependencies:

- `sqlalchemy`: Database ORM
- `tqdm`: Progress bars
- `edge-tts`: Microsoft Edge TTS (preferred)
- `gtts`: Google TTS (fallback)
- `aiohttp`: Async HTTP client
- `zstandard`: Archive compression

Install all dependencies:

```bash
pip install sqlalchemy tqdm edge-tts gtts aiohttp zstandard
```

## Security Considerations

- Mock users have limited permissions
- Export batches include checksums for integrity
- Download rate limiting prevents abuse
- Signed URLs for secure R2 downloads
- File permissions set to owner-only (600)

## Monitoring

The scripts provide comprehensive logging and metrics:

- Processing statistics and timing
- Quality score distributions
- Export batch success/failure rates
- Download tracking and limits
- Storage usage monitoring (R2 free tier)

Use the output logs to monitor system health and identify bottlenecks in the workflow.
