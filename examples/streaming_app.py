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
Enhanced Streaming Gradio app for Kokoro TTS with multi-language support

Download model files:
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

Run with:
uv run examples/streaming_app.py
"""

import gradio as gr
import numpy as np
import PyPDF2
import time

from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer

tokenizer = Tokenizer()
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")

# Voice database organized by language and quality
VOICE_DATABASE = {
    "American English": {
        "code": "en-us",
        "voices": {
            "High Quality": {
                "female": ["af_heart", "af_bella"],
                "male": []
            },
            "Medium Quality": {
                "female": ["af_nicole", "af_aoede", "af_kore", "af_sarah"],
                "male": ["am_fenrir", "am_michael", "am_puck"]
            },
            "Low Quality": {
                "female": ["af_alloy", "af_jessica", "af_nova", "af_river", "af_sky"],
                "male": ["am_adam", "am_echo", "am_eric", "am_liam", "am_onyx", "am_santa"]
            }
        }
    },
    "British English": {
        "code": "en-gb",
        "voices": {
            "Medium Quality": {
                "female": ["bf_alice", "bf_emma", "bf_isabella", "bf_lily"],
                "male": ["bm_daniel", "bm_fable", "bm_george", "bm_lewis"]
            }
        }
    },
    "Japanese": {
        "code": "ja",
        "voices": {
            "Medium Quality": {
                "female": ["jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro"],
                "male": ["jm_kumo"]
            }
        }
    },
    "Mandarin Chinese": {
        "code": "cmn",
        "voices": {
            "Low Quality": {
                "female": ["zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi"],
                "male": ["zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"]
            }
        }
    },
    "Spanish": {
        "code": "es",
        "voices": {
            "Medium Quality": {
                "female": ["ef_dora"],
                "male": ["em_alex", "em_santa"]
            }
        }
    },
    "French": {
        "code": "fr-fr",
        "voices": {
            "Medium Quality": {
                "female": ["ff_siwis"],
                "male": []
            }
        }
    },
    "Hindi": {
        "code": "hi",
        "voices": {
            "Medium Quality": {
                "female": ["hf_alpha", "hf_beta"],
                "male": ["hm_omega", "hm_psi"]
            }
        }
    },
    "Italian": {
        "code": "it",
        "voices": {
            "Medium Quality": {
                "female": ["if_sara"],
                "male": ["im_nicola"]
            }
        }
    },
    "Brazilian Portuguese": {
        "code": "pt-br",
        "voices": {
            "Medium Quality": {
                "female": ["pf_dora"],
                "male": ["pm_alex", "pm_santa"]
            }
        }
    }
}

def get_language_code(language_name: str) -> str:
    """Get language code from display name"""
    return VOICE_DATABASE.get(language_name, {}).get("code", "en-us")

def get_voices_for_language_and_quality(language_name: str, quality_name: str = "All Qualities", gender_filter: str = "All Genders") -> list[str]:
    """Get voices filtered by language name, quality name, and gender"""
    if language_name not in VOICE_DATABASE:
        return []
    
    voices = []
    lang_data = VOICE_DATABASE[language_name]["voices"]
    
    for quality_level, genders in lang_data.items():
        if quality_name == "All Qualities" or quality_name == quality_level:
            for gender, voice_list in genders.items():
                # Filter by gender
                if gender_filter == "All Genders" or gender_filter.lower() == gender:
                    voices.extend(voice_list)
    
    return sorted(voices)

def get_available_qualities_for_language(language_name: str) -> list[str]:
    """Get available quality levels for a language"""
    if language_name not in VOICE_DATABASE:
        return ["All Qualities"]
    
    qualities = list(VOICE_DATABASE[language_name]["voices"].keys())
    return ["All Qualities"] + qualities

def get_available_genders_for_language(language_name: str, quality_name: str = "All Qualities") -> list[str]:
    """Get available genders for a language and quality combination"""
    if language_name not in VOICE_DATABASE:
        return ["All Genders"]
    
    genders = set()
    lang_data = VOICE_DATABASE[language_name]["voices"]
    
    for quality_level, gender_data in lang_data.items():
        if quality_name == "All Qualities" or quality_name == quality_level:
            for gender, voice_list in gender_data.items():
                if voice_list:  # Only include genders that have voices
                    genders.add(gender.title())  # Capitalize: female -> Female
    
    gender_list = ["All Genders"] + sorted(list(genders))
    return gender_list

def create_streaming_app():
    with gr.Blocks(
        theme=gr.themes.Soft(font=[gr.themes.GoogleFont("Roboto")]),
        title="Kokoro TTS Streaming"
    ) as ui:
        
        gr.Markdown("# 🎵 Kokoro TTS Streaming")
        gr.Markdown("### Multi-language Text-to-Speech with Advanced Filtering")
        gr.Markdown("Filter by **language**, **quality level**, and **gender** to find the perfect voice from 149 options across 9+ languages!")
        
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Tab("Text Input"):
                    text_input = gr.TextArea(
                        label="Input Text",
                        placeholder="Enter text to convert to speech...",
                        value="Kokoro TTS streaming demo. Real-time speech synthesis!",
                        lines=4
                    )
                
                with gr.Tab("File Upload"):
                    file_input = gr.File(
                        label="Upload Text/PDF File",
                        file_types=[".txt", ".md", ".rtf", ".pdf"],
                        file_count="single"
                    )
                    file_text_display = gr.TextArea(
                        label="File Content",
                        placeholder="File content will appear here...",
                        lines=4,
                        interactive=False
                    )
                
                with gr.Row():
                    language_input = gr.Dropdown(
                        label="Language",
                        value="American English",
                        choices=list(VOICE_DATABASE.keys()),
                        scale=1
                    )
                    
                    quality_input = gr.Dropdown(
                        label="Quality Level",
                        value="All Qualities",
                        choices=get_available_qualities_for_language("American English"),
                        scale=1
                    )
                    
                    gender_input = gr.Dropdown(
                        label="Gender",
                        value="All Genders",
                        choices=get_available_genders_for_language("American English", "All Qualities"),
                        scale=1
                    )
                
                voice_input = gr.Dropdown(
                    label="Voice",
                    value="af_sky",
                    choices=get_voices_for_language_and_quality("American English", "All Qualities", "All Genders"),
                    scale=2
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
                metrics_display = gr.Markdown(
                    value="*Generate audio to see processing metrics*",
                    visible=True
                )
        
        # Update quality choices when language changes
        def update_quality_choices(language_name):
            qualities = get_available_qualities_for_language(language_name)
            return gr.update(choices=qualities, value="All Qualities")
        
        # Update gender choices when language or quality changes
        def update_gender_choices(language_name, quality_name):
            genders = get_available_genders_for_language(language_name, quality_name)
            return gr.update(choices=genders, value="All Genders")
        
        # Update voice choices when language, quality, or gender changes
        def update_voice_choices(language_name, quality_name, gender_name):
            voices = get_voices_for_language_and_quality(language_name, quality_name, gender_name)
            if voices:
                return gr.update(choices=voices, value=voices[0])
            return gr.update(choices=[], value=None)
        
        # Handle file upload
        def handle_file_upload(file):
            if file is None:
                return ""
            
            try:
                file_path = file.name
                file_extension = file_path.lower().split('.')[-1]
                content = ""
                
                if file_extension == 'pdf':
                    # Handle PDF files
                    try:
                        with open(file_path, 'rb') as pdf_file:
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            text_parts = []
                            
                            for page_num in range(len(pdf_reader.pages)):
                                page = pdf_reader.pages[page_num]
                                text_parts.append(page.extract_text())
                            
                            content = '\n'.join(text_parts)
                            
                    except Exception as pdf_error:
                        gr.Warning(f"Error reading PDF: {str(pdf_error)}")
                        return ""
                        
                else:
                    # Handle text files - try different encodings
                    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                    
                    for encoding in encodings:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                
                if not content:
                    gr.Warning("Could not extract text from file. Please ensure it's a valid text or PDF file.")
                    return ""
                
                # Limit content length for performance
                max_chars = 10000
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n\n[Content truncated - file too long]"
                    gr.Info(f"File content truncated to {max_chars} characters for performance")
                
                return content
                
            except Exception as e:
                gr.Warning(f"Error reading file: {str(e)}")
                return ""
        
        # Handle button click
        async def handle_generate(text, file_content, voice, language_name, speed):
            # Use file content if available, otherwise use text input
            input_text = file_content.strip() if file_content.strip() else text.strip()
            
            if not input_text:
                gr.Warning("Please enter text or upload a file")
                return None, ""
                
            if not voice:
                gr.Warning("Please select a voice")
                return None, ""
                
            try:
                # Start timing
                start_time = time.time()
                
                language_code = get_language_code(language_name)
                
                # Use streaming for faster generation but collect all chunks
                stream = kokoro.create_stream(
                    input_text,
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
                
                # Calculate timing and metrics
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Return complete audio and metrics
                if all_samples:
                    complete_audio = np.concatenate(all_samples)
                    audio_duration = len(complete_audio) / sample_rate
                    
                    # Format metrics
                    metrics_text = f"""**Generation Metrics:**
- Processing Time: {processing_time:.2f} seconds
- Audio Duration: {audio_duration:.2f} seconds
- Speed Ratio: {audio_duration/processing_time:.1f}x real-time
- Sample Rate: {sample_rate:,} Hz
- Audio Samples: {len(complete_audio):,}"""
                    
                    return (sample_rate, complete_audio), metrics_text
                else:
                    return None, ""
                    
            except Exception as e:
                gr.Error(f"Error generating audio: {str(e)}")
                return None, ""
        
        # Update quality dropdown when language changes
        language_input.change(
            fn=update_quality_choices,
            inputs=[language_input],
            outputs=[quality_input]
        )
        
        # Update gender dropdown when language or quality changes
        language_input.change(
            fn=update_gender_choices,
            inputs=[language_input, quality_input],
            outputs=[gender_input]
        )
        
        quality_input.change(
            fn=update_gender_choices,
            inputs=[language_input, quality_input],
            outputs=[gender_input]
        )
        
        # Update voice dropdown when language, quality, or gender changes
        language_input.change(
            fn=update_voice_choices,
            inputs=[language_input, quality_input, gender_input],
            outputs=[voice_input]
        )
        
        quality_input.change(
            fn=update_voice_choices,
            inputs=[language_input, quality_input, gender_input],
            outputs=[voice_input]
        )
        
        gender_input.change(
            fn=update_voice_choices,
            inputs=[language_input, quality_input, gender_input],
            outputs=[voice_input]
        )
        
        # Connect file upload to display content
        file_input.change(
            fn=handle_file_upload,
            inputs=[file_input],
            outputs=[file_text_display]
        )
        
        generate_btn.click(
            fn=handle_generate,
            inputs=[text_input, file_text_display, voice_input, language_input, speed_input],
            outputs=[audio_output, metrics_display]
        )
        
        # Add example texts in multiple languages with human readable names
        gr.Examples(
            examples=[
                ["Hello, this is a test of Kokoro TTS streaming capabilities.", "af_sky", "American English", "All Qualities", "All Genders", 1.0],
                ["The quick brown fox jumps over the lazy dog.", "af_bella", "American English", "High Quality", "Female", 1.2],
                ["Welcome to the future of text-to-speech technology!", "af_sarah", "American English", "Medium Quality", "Female", 0.9],
                ["Good morning! How are you today?", "bf_alice", "British English", "Medium Quality", "Female", 1.0],
                ["こんにちは、元気ですか？", "jf_alpha", "Japanese", "Medium Quality", "Female", 1.0],
                ["Bonjour, comment allez-vous?", "ff_siwis", "French", "Medium Quality", "Female", 1.0],
            ],
            inputs=[text_input, voice_input, language_input, quality_input, gender_input, speed_input],
        )
        
    return ui


if __name__ == "__main__":
    app = create_streaming_app()
    app.launch(debug=True, share=False)