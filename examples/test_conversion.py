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
Simple test script to verify audio conversion functionality works.
Tests the conversion utility without requiring ffmpeg binary.

Run with:
uv run examples/test_conversion.py
"""

import numpy as np
from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer

# Test basic functionality without conversion first
def test_basic_generation():
    """Test basic audio generation works."""
    print("Testing basic audio generation...")
    try:
        tokenizer = Tokenizer()
        kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
        
        text = "Hello world"
        phonemes = tokenizer.phonemize(text, lang="en-us")
        samples, sample_rate = kokoro.create(phonemes, voice="af_sky", speed=1.0, is_phonemes=True)
        
        print(f"✓ Generated audio: {len(samples)} samples at {sample_rate}Hz")
        print(f"✓ Audio duration: {len(samples)/sample_rate:.2f} seconds")
        return samples, sample_rate
    except Exception as e:
        print(f"✗ Basic generation failed: {e}")
        return None, None

def test_conversion_import():
    """Test if conversion module can be imported."""
    print("\nTesting conversion module import...")
    try:
        from kokoro_onnx.convert import SUPPORTED_FORMATS, BITRATE_OPTIONS, save_audio_as
        print(f"✓ Supported formats: {list(SUPPORTED_FORMATS.keys())}")
        print(f"✓ Bitrate options: {BITRATE_OPTIONS}")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_wav_save():
    """Test WAV saving (should work without ffmpeg)."""
    print("\nTesting WAV file save...")
    try:
        from kokoro_onnx.convert import save_audio_as
        
        # Generate test audio
        samples, sample_rate = test_basic_generation()
        if samples is None:
            return False
            
        # Save as WAV (uses soundfile, no ffmpeg needed)
        save_audio_as(samples, sample_rate, "test_output", "wav")
        print("✓ WAV save completed (check test_output.wav)")
        return True
    except Exception as e:
        print(f"✗ WAV save failed: {e}")
        return False

def test_ffmpeg_dependency():
    """Test if ffmpeg-python is available."""
    print("\nTesting ffmpeg-python dependency...")
    try:
        import ffmpeg
        print("✓ ffmpeg-python imported successfully")
        
        # Test basic ffmpeg functionality
        input_stream = ffmpeg.input("dummy.wav")
        output_stream = ffmpeg.output(input_stream, "dummy.mp3")
        print("✓ ffmpeg stream creation works")
        return True
    except ImportError as e:
        print(f"✗ ffmpeg-python import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠ ffmpeg-python imported but stream creation failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Audio Conversion Test Suite ===\n")
    
    # Run tests
    basic_works = test_basic_generation()[0] is not None
    import_works = test_conversion_import()
    wav_works = test_wav_save()
    ffmpeg_works = test_ffmpeg_dependency()
    
    print(f"\n=== Test Results ===")
    print(f"Basic generation: {'✓' if basic_works else '✗'}")
    print(f"Conversion import: {'✓' if import_works else '✗'}")
    print(f"WAV save: {'✓' if wav_works else '✗'}")
    print(f"ffmpeg-python: {'✓' if ffmpeg_works else '✗'}")
    
    if basic_works and import_works and wav_works:
        print(f"\n✓ Core functionality working!")
        if not ffmpeg_works:
            print("⚠ Note: ffmpeg binary needed for MP3/M4A/FLAC conversion")
            print("  Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)")
    else:
        print(f"\n✗ Some core functionality failed")