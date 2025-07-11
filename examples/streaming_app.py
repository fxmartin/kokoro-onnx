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
Streaming Gradio app for Kokoro TTS

Download model files:
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

Run with:
uv run examples/streaming_app.py
"""

import asyncio
import io

import gradio as gr
import soundfile as sf

from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer

tokenizer = Tokenizer()
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")

SUPPORTED_LANGUAGES = ["en-us"]


async def stream_audio(text: str, voice: str, language: str = "en-us", speed: float = 1.0):
    """Stream audio generation asynchronously"""
    if not text.strip():
        return
    
    try:
        async for audio_chunk, sample_rate in kokoro.create_stream(
            text, voice=voice, speed=speed, lang=language
        ):
            # Convert numpy array to audio bytes
            buffer = io.BytesIO()
            sf.write(buffer, audio_chunk, sample_rate, format='WAV')
            buffer.seek(0)
            
            # Yield the audio data
            yield (sample_rate, audio_chunk)
            
            # Small delay to allow UI updates
            await asyncio.sleep(0.01)
            
    except Exception as e:
        print(f"Error during streaming: {e}")


def create_streaming_app():
    with gr.Blocks(
        theme=gr.themes.Soft(font=[gr.themes.GoogleFont("Roboto")]),
        title="Kokoro TTS Streaming"
    ) as ui:
        
        gr.Markdown("# 🎵 Kokoro TTS Streaming")
        gr.Markdown("Enter text and select a voice to generate streaming audio")
        
        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.TextArea(
                    label="Input Text",
                    placeholder="Enter text to convert to speech...",
                    value="Kokoro TTS streaming demo. Real-time speech synthesis!",
                    lines=4
                )
                
                with gr.Row():
                    voice_input = gr.Dropdown(
                        label="Voice",
                        value="af_sky",
                        choices=sorted(kokoro.get_voices()),
                        scale=2
                    )
                    
                    language_input = gr.Dropdown(
                        label="Language",
                        value="en-us",
                        choices=SUPPORTED_LANGUAGES,
                        scale=1
                    )
                
                speed_input = gr.Slider(
                    label="Speed",
                    minimum=0.5,
                    maximum=2.0,
                    value=1.0,
                    step=0.1
                )
                
                generate_btn = gr.Button("🎤 Generate Speech", variant="primary")
                
            with gr.Column(scale=1):
                audio_output = gr.Audio(
                    label="Generated Audio",
                    streaming=True,
                    autoplay=True
                )
        
        # Handle button click with streaming
        async def handle_generate(text, voice, language, speed):
            if not text.strip():
                gr.Warning("Please enter some text")
                return None
                
            try:
                # Use the regular create method for now since Gradio streaming has limitations
                phonemes = tokenizer.phonemize(text, lang=language)
                samples, sample_rate = kokoro.create(
                    phonemes, voice=voice, speed=speed, is_phonemes=True
                )
                return (sample_rate, samples)
            except Exception as e:
                gr.Error(f"Error generating audio: {str(e)}")
                return None
        
        generate_btn.click(
            fn=handle_generate,
            inputs=[text_input, voice_input, language_input, speed_input],
            outputs=[audio_output]
        )
        
        # Add example texts
        gr.Examples(
            examples=[
                ["Hello, this is a test of Kokoro TTS streaming capabilities.", "af_sky", "en-us", 1.0],
                ["The quick brown fox jumps over the lazy dog.", "af_bella", "en-us", 1.2],
                ["Welcome to the future of text-to-speech technology!", "af_sarah", "en-us", 0.9],
            ],
            inputs=[text_input, voice_input, language_input, speed_input],
        )
        
    return ui


if __name__ == "__main__":
    app = create_streaming_app()
    app.launch(debug=True, share=False)