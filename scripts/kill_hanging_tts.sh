#!/bin/bash

# Kill hanging TTS generation script
# This script finds and kills the generate_test_data.py process if it's hanging

echo "🔍 Looking for hanging TTS generation process..."

# Find the process
PID=$(docker exec voice_collection_backend pgrep -f "generate_test_data.py" 2>/dev/null)

if [ -z "$PID" ]; then
    echo "✅ No hanging TTS process found"
    exit 0
fi

echo "🛑 Found hanging process with PID: $PID"
echo "   Killing it now..."

# Kill the process
docker exec voice_collection_backend kill -9 $PID 2>/dev/null

# Verify it's gone
sleep 2
NEW_PID=$(docker exec voice_collection_backend pgrep -f "generate_test_data.py" 2>/dev/null)

if [ -z "$NEW_PID" ]; then
    echo "✅ Process killed successfully"
else
    echo "⚠️  Process still running, trying harder..."
    docker exec voice_collection_backend pkill -9 -f "generate_test_data.py"
    sleep 1
    FINAL_CHECK=$(docker exec voice_collection_backend pgrep -f "generate_test_data.py" 2>/dev/null)
    if [ -z "$FINAL_CHECK" ]; then
        echo "✅ Process killed successfully"
    else
        echo "❌ Could not kill process. You may need to restart the container."
    fi
fi

echo ""
echo "💡 The script has been updated with timeout fixes to prevent future hanging."
echo "   Try running it again - it should work now!"
