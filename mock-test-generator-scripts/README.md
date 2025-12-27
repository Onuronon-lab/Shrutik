## Mock Test Generator Scripts

This directory contains scripts for generating test data and testing the complete voice collection and export workflow.


## How to Run

You can run the scripts in one of two ways:

-   **Docker (recommended)**  
    Scripts are executed inside the backend container. No Local configuration is required.
    
-   **Local execution**  
    Scripts are run directly on the host machine. Environment variables must be set manually.
    


###  Cleanup Test Data
If test data already exists, clean it before starting:

**Docker**
```
docker exec -it voice_collection_backend \
python mock-test-generator-scripts/cleanup_generated_data.py
```
**Local**
```
python mock-test-generator-scripts/cleanup_generated_data.py
```
---
###  Generate Data

#### `generate_test_data.py`

Generates synthetic voice recordings using Text-to-Speech (TTS).

-   Creates motivational scripts
    
-   Uses Edge TTS (preferred) or Google TTS (fallback)
    
-   Stores recordings and metadata in PostgreSQL
    
-   Uses Docker-compatible file paths
    

**Docker:**

```bash
docker exec -it voice_collection_backend \
python mock-test-generator-scripts/generate_test_data.py

```

**Local:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python generate_test_data.py

```
You can now verify in **DBeaver** or  any database viewer:
```
Schemas → public → Tables
- voice_recordings
- scripts
```

### Trigger Audio Processing 
 `trigger_audio_processing.py`

Triggers Celery tasks to process uploaded recordings into audio chunks.

-   Queues unprocessed recordings
    
-   Supports batch processing
    
-   Provides basic processing statistics
    

**Docker:**

```bash
docker exec -it voice_collection_backend \
python mock-test-generator-scripts/trigger_audio_processing.py

```

**Local:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python trigger_audio_processing.py

```

When prompted,  select **all unprocessed data** and proceed
After completion, check:
```
Schemas → public → Tables
- audio_chunks

```

### Generate Mock Transcriptions

#### `generate_mock_transcriptions.py`

Generates mock transcriptions for processed audio chunks.

What this does:

-   Creates 5–8 transcriptions per chunk
    
-   Simulates real users
    
-   Adds typos, punctuation, casing variations
    
-   Calculates individual quality scores
    

Database tables affected:

-   `transcriptions`
    

**Docker:**

```bash
docker exec -it voice_collection_backend \
python mock-test-generator-scripts/generate_mock_transcriptions.py

```

**Local:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python generate_mock_transcriptions.py

```
---

### Prepare Export Data 

`prepare_export_data.py`

Calculates transcription consensus and marks chunks ready for export.

-   Requires at least 5 transcriptions per chunk
    
-   Applies a quality threshold of 90%
    
-   Marks eligible chunks as `ready_for_export`
    

**Docker:**

```bash
docker exec -it voice_collection_backend \
python mock-test-generator-scripts/prepare_export_data.py

```

**Local:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python prepare_export_data.py

```

Tables updated:

-   `audio_chunks`
    

### Test Export Workflow 

 `test_export_workflow.py`

Tests the export workflow end-to-end.

-   Creates export batches
    
-   Validates exported files and metadata
    
-   Tests download limits and rate limiting
    
-   Supports both local storage and R2 storage
    

**Docker:**

```bash
docker exec -it voice_collection_backend \
python mock-test-generator-scripts/test_export_workflow.py

```

**Local:**

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection \
python test_export_workflow.py

```

This validates:

-   Export batch creation
    
-   File packaging and compression
    
-   Download limits and metadata
    
-   Local or R2 storage handling
    

After this step, mock data can be safely discarded.


## Download the Data

Once all data has been generated and processed:

1.  Open your browser and go to `http://localhost:3000`.
    
2.  Log in as **Admin**.
    
3.  Navigate to the **Export Data** section.
    
4.  You will see all processed audio chunks marked as ready for export.
    
5.  Download the files and test them as needed.
    

> Note: Ensure the backend container is running while accessing the web interface.


## Complete Workflow

1.  **Generate Test Data**  
    Create synthetic voice recordings and store them in the database.
    
2.  **Process Audio**  
    Split recordings into audio chunks ready for transcription.
    
3.  **Generate Mock Transcriptions**  
    Simulate user transcriptions for each audio chunk, including small variations and typos.
    
4.  **Prepare Export Data**  
    Calculate consensus for transcriptions and mark chunks as ready for export.
    
5.  **Test Export Workflow**  
    Validate that export batches are correctly packaged, metadata is accurate, and download limits are enforced.
    
6.  **Download Data**  
    Access the exported audio chunks through the web interface (`localhost:3000`) or your preferred storage.
    

> You can run all these steps either inside Docker (recommended) or locally on your machine with the proper database configuration.


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

### Docker

When running scripts using `docker exec`:

-   Database and Redis are configured via Docker Compose
    
-   No environment variables need to be set manually
    

### Local

When running scripts locally, set the following variables:

-   `DATABASE_URL` – PostgreSQL connection string
    
-   `REDIS_URL` – Redis connection (default: `redis://localhost:6379/0`)
    
-   `AUDIO_OUTPUT_DIR` – Optional custom audio output directory
    
-   `LOG_LEVEL=DEBUG` – Optional verbose logging
    


## Storage

Export functionality supports:

**Local Storage**

-   Files stored in `uploads/exports/`
    
-   Direct file downloads
    

**R2 (Cloudflare) Storage**

-   Files uploaded to R2 buckets
    
-   Signed URLs for secure downloads
    

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


