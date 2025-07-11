# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "gradio>=5.13.1",
#     "kokoro-onnx>=0.3.8",
# ]
#
# [tool.uv.sources]
# kokoro-onnx = { path = "../" }
# ///

"""
Enhanced Kokoro TTS app with audio format conversion support

Download model files:
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

Run with:
uv run examples/app_with_conversion.py
"""

import gradio as gr
import numpy as np
import tempfile
import os

from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer
from kokoro_onnx.convert import convert_audio, SUPPORTED_FORMATS, BITRATE_OPTIONS

tokenizer = Tokenizer()
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")

SUPPORTED_LANGUAGES = ["en-us"]


def create_audio(
    text: str, 
    voice: str, 
    language: str, 
    output_format: str = "wav",
    bitrate: str = "128k",
    blend_voice_name: str = None
):
    """Create audio with specified format conversion."""
    phonemes = tokenizer.phonemize(text, lang=language)

    # Voice blending
    if blend_voice_name:
        first_voice = kokoro.get_voice_style(voice)
        second_voice = kokoro.get_voice_style(blend_voice_name)
        voice = np.add(first_voice * (50 / 100), second_voice * (50 / 100))
    
    # Generate audio
    samples, sample_rate = kokoro.create(
        phonemes, voice=voice, speed=1.0, is_phonemes=True
    )
    
    # Convert to requested format if not WAV
    if output_format.lower() == "wav":
        # Return standard WAV for Gradio
        return [(sample_rate, samples), phonemes, None]
    else:
        # Convert to requested format and create downloadable file
        try:
            audio_data = convert_audio(samples, sample_rate, output_format, bitrate)
            
            # Create temporary file for download
            with tempfile.NamedTemporaryFile(
                suffix=f".{output_format}", 
                delete=False
            ) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            return [
                (sample_rate, samples),  # Preview audio (WAV for Gradio)
                phonemes,
                temp_file_path  # Download file
            ]
        except Exception as e:
            return [
                (sample_rate, samples),
                phonemes,
                f"Conversion error: {str(e)}"
            ]


def create_app():
    with gr.Blocks(theme=gr.themes.Soft(font=[gr.themes.GoogleFont("Roboto")])) as ui:
        gr.Markdown("# Kokoro TTS with Audio Format Conversion")
        gr.Markdown("Generate speech and download in various audio formats")
        
        with gr.Row():
            with gr.Column():
                text_input = gr.TextArea(
                    label="Input Text",
                    rtl=False,
                    value="Kokoro TTS. Turning words into emotion, one voice at a time!",
                )
                
                with gr.Row():
                    language_input = gr.Dropdown(
                        label="Language",
                        value="en-us",
                        choices=SUPPORTED_LANGUAGES,
                    )
                    voice_input = gr.Dropdown(
                        label="Voice", 
                        value="af_sky", 
                        choices=sorted(kokoro.get_voices())
                    )
                
                blend_voice_input = gr.Dropdown(
                    label="Blend Voice (Optional)",
                    value=None,
                    choices=sorted(kokoro.get_voices()) + [None],
                )
                
                with gr.Row():
                    format_input = gr.Dropdown(
                        label="Output Format",
                        value="wav",
                        choices=[(f"{info['name']} (.{info['extension']})", key) 
                                for key, info in SUPPORTED_FORMATS.items()],
                    )
                    bitrate_input = gr.Dropdown(
                        label="Bitrate (for lossy formats)",
                        value="128k",
                        choices=BITRATE_OPTIONS,
                    )
                
                submit_button = gr.Button("Generate Audio", variant="primary")
            
            with gr.Column():
                audio_output = gr.Audio(label="Audio Preview")
                phonemes_output = gr.Textbox(label="Phonemes")
                download_output = gr.File(
                    label="Download Audio File",
                    visible=True
                )
        
        # Format info
        gr.Markdown("""
        ### Format Information:
        - **WAV**: Uncompressed, highest quality, larger file size
        - **FLAC**: Lossless compression, high quality, moderate file size  
        - **MP3**: Lossy compression, good quality, small file size
        - **M4A/AAC**: Lossy compression, good quality, small file size
        - **OGG**: Lossy compression, good quality, small file size
        
        *Bitrate setting only affects lossy formats (MP3, M4A, OGG)*
        """)
        
        submit_button.click(
            fn=create_audio,
            inputs=[
                text_input, 
                voice_input, 
                language_input, 
                format_input,
                bitrate_input,
                blend_voice_input
            ],
            outputs=[audio_output, phonemes_output, download_output],
        )
        
    return ui


if __name__ == "__main__":
    ui = create_app()
    ui.launch(debug=True)