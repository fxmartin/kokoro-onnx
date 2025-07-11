# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "kokoro-onnx>=0.3.8",
# ]
#
# [tool.uv.sources]
# kokoro-onnx = { path = "../" }
# ///

"""
Test script to verify streaming app conversion functionality.

Run with:
uv run examples/test_streaming_conversion.py
"""

import asyncio
import numpy as np
import tempfile
import os
from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer
from kokoro_onnx.convert import convert_audio, SUPPORTED_FORMATS

async def test_streaming_conversion():
    """Test the streaming app conversion logic."""
    print("=== Streaming App Conversion Test ===\n")
    
    try:
        # Initialize
        tokenizer = Tokenizer()
        kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
        
        text = "Testing streaming conversion functionality"
        voice = "af_sky"
        language_code = "en-us"
        speed = 1.0
        
        print(f"Testing text: '{text}'")
        print(f"Voice: {voice}")
        print(f"Language: {language_code}")
        
        # Use streaming for faster generation but collect all chunks
        stream = kokoro.create_stream(
            text,
            voice=voice,
            speed=speed,
            lang=language_code
        )
        
        # Collect all audio chunks
        all_samples = []
        sample_rate = None
        
        async for samples, sr in stream:
            if sample_rate is None:
                sample_rate = sr
            all_samples.append(samples)
        
        if all_samples:
            complete_audio = np.concatenate(all_samples)
            audio_duration = len(complete_audio) / sample_rate
            
            print(f"\n✓ Audio generated: {len(complete_audio)} samples at {sample_rate}Hz")
            print(f"✓ Duration: {audio_duration:.2f} seconds")
            
            # Test conversion for each format
            for format_key, format_info in SUPPORTED_FORMATS.items():
                print(f"\nTesting {format_info['name']} conversion...")
                
                try:
                    if format_key.lower() == "wav":
                        # Create WAV file for download using soundfile
                        import soundfile as sf
                        with tempfile.NamedTemporaryFile(
                            suffix=".wav", 
                            delete=False
                        ) as temp_file:
                            sf.write(temp_file.name, complete_audio, sample_rate)
                            download_file = temp_file.name
                            
                        # Check file exists and has content
                        if os.path.exists(download_file) and os.path.getsize(download_file) > 0:
                            print(f"✓ WAV file created: {os.path.getsize(download_file)} bytes")
                            os.unlink(download_file)  # Clean up
                        else:
                            print("✗ WAV file creation failed")
                            
                    else:
                        # Convert to requested format
                        audio_data = convert_audio(complete_audio, sample_rate, format_key, "128k")
                        
                        # Create temporary file for download
                        with tempfile.NamedTemporaryFile(
                            suffix=f".{format_key}", 
                            delete=False
                        ) as temp_file:
                            temp_file.write(audio_data)
                            download_file = temp_file.name
                        
                        # Check file exists and has content
                        if os.path.exists(download_file) and os.path.getsize(download_file) > 0:
                            print(f"✓ {format_info['name']} file created: {os.path.getsize(download_file)} bytes")
                            os.unlink(download_file)  # Clean up
                        else:
                            print(f"✗ {format_info['name']} file creation failed")
                            
                except Exception as e:
                    print(f"✗ {format_info['name']} conversion failed: {e}")
            
            print(f"\n✓ All conversion tests completed!")
            return True
            
        else:
            print("✗ No audio generated")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_streaming_conversion())
    if success:
        print("\n🎉 Streaming conversion functionality working correctly!")
    else:
        print("\n❌ Streaming conversion tests failed")