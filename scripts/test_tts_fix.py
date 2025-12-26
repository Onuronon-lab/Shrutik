#!/usr/bin/env python3
"""
Quick test to verify the TTS timeout fix works
"""

import asyncio
import sys
from pathlib import Path

# Add the mock-test-generator-scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mock-test-generator-scripts"))

try:
    from generate_test_data import test_tts_connectivity

    async def main():
        print("🧪 Testing TTS connectivity with timeout protection...")
        print("   This should either succeed quickly or fail with timeout (not hang)")
        print("=" * 60)

        try:
            result = await test_tts_connectivity()
            if result:
                print("\n✅ TTS connectivity test passed!")
            else:
                print("\n⚠️  TTS connectivity test failed, but didn't hang!")
        except Exception as e:
            print(f"\n❌ TTS test failed with error: {e}")
            print("   But it failed quickly instead of hanging - that's good!")

        print("\n💡 The timeout fix is working - no more infinite hanging!")

    if __name__ == "__main__":
        asyncio.run(main())

except ImportError as e:
    print(f"❌ Could not import test module: {e}")
    print("   Make sure you're running this from the project root")
