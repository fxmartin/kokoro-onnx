"""Audio format conversion utilities using ffmpeg."""

import tempfile
import os
from pathlib import Path
from typing import Tuple
import numpy as np
import soundfile as sf
import ffmpeg


def convert_audio(
    samples: np.ndarray,
    sample_rate: int,
    output_format: str = "wav",
    bitrate: str = "128k"
) -> bytes:
    """
    Convert audio samples to specified format using ffmpeg.
    
    Args:
        samples: Audio samples as numpy array
        sample_rate: Sample rate of the audio
        output_format: Target format (mp3, m4a, flac, ogg, wav)
        bitrate: Bitrate for lossy formats (e.g., "128k", "192k", "320k")
        
    Returns:
        bytes: Converted audio data
    """
    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as temp_output:
            try:
                # Write samples to temporary WAV file
                sf.write(temp_wav.name, samples, sample_rate)
                
                # Convert using ffmpeg
                if output_format.lower() in ["mp3", "m4a", "ogg"]:
                    # Lossy formats with bitrate
                    (
                        ffmpeg
                        .input(temp_wav.name)
                        .output(temp_output.name, audio_bitrate=bitrate)
                        .overwrite_output()
                        .run(quiet=True)
                    )
                else:
                    # Lossless formats (flac, wav)
                    (
                        ffmpeg
                        .input(temp_wav.name)
                        .output(temp_output.name)
                        .overwrite_output()
                        .run(quiet=True)
                    )
                
                # Read converted file
                with open(temp_output.name, "rb") as f:
                    return f.read()
                    
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_wav.name)
                    os.unlink(temp_output.name)
                except OSError:
                    pass


def save_audio_as(
    samples: np.ndarray,
    sample_rate: int,
    filename: str,
    output_format: str = "wav",
    bitrate: str = "128k"
) -> None:
    """
    Save audio samples to file in specified format.
    
    Args:
        samples: Audio samples as numpy array
        sample_rate: Sample rate of the audio
        filename: Output filename (extension will be replaced if needed)
        output_format: Target format (mp3, m4a, flac, ogg, wav)
        bitrate: Bitrate for lossy formats
    """
    # Ensure filename has correct extension
    path = Path(filename)
    output_path = path.with_suffix(f".{output_format}")
    
    if output_format.lower() == "wav":
        # Use soundfile for WAV (faster)
        sf.write(str(output_path), samples, sample_rate)
    else:
        # Use ffmpeg for other formats
        audio_data = convert_audio(samples, sample_rate, output_format, bitrate)
        with open(output_path, "wb") as f:
            f.write(audio_data)


# Supported formats and their properties
SUPPORTED_FORMATS = {
    "wav": {"name": "WAV", "extension": "wav", "lossy": False},
    "mp3": {"name": "MP3", "extension": "mp3", "lossy": True},
    "m4a": {"name": "M4A/AAC", "extension": "m4a", "lossy": True},
    "flac": {"name": "FLAC", "extension": "flac", "lossy": False},
    "ogg": {"name": "OGG Vorbis", "extension": "ogg", "lossy": True},
}

# Bitrate options for lossy formats
BITRATE_OPTIONS = ["96k", "128k", "192k", "256k", "320k"]