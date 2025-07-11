"""
Kokoro TTS Main Application

A comprehensive streaming Gradio app for Kokoro TTS with multi-language support.

Download model files:
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

Run with:
python main.py
"""

import os
import tempfile
import time
from datetime import datetime

import gradio as gr
import PyPDF2
from dotenv import load_dotenv

from kokoro_onnx import Kokoro
from kokoro_onnx.convert import SUPPORTED_FORMATS, convert_audio
from kokoro_onnx.tokenizer import Tokenizer
from logger import Logger

# Load environment variables from .env file
load_dotenv()

# Initialize enhanced logger with file logging
def setup_enhanced_logging():
    """Set up enhanced logging with both console and file output"""
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"kokoro_app_{timestamp}.log")
    
    # Create logger instance with enhanced features
    logger = Logger("kokoro_app", level=log_level)
    
    # Add file handler to the underlying logger for persistent logging
    import logging
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level, logging.DEBUG))
    
    # File format with more details
    file_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    file_formatter = logging.Formatter(file_format)
    file_handler.setFormatter(file_formatter)
    
    logger.logger.addHandler(file_handler)
    
    # Check if .env file exists and log configuration source
    env_file_exists = os.path.exists(".env")
    config_source = ".env file" if env_file_exists else "environment variables/defaults"
    
    logger.info(f"Enhanced logging initialized - Level: {log_level} (from {config_source})")
    logger.info(f"Log file: {log_file}")
    
    if env_file_exists:
        logger.debug("Configuration loaded from .env file")
    else:
        logger.debug("No .env file found, using environment variables and defaults")
        logger.debug("Create a .env file to customize configuration (see .env.example)")
    
    return logger

# Initialize enhanced logging
logger = setup_enhanced_logging()

tokenizer = Tokenizer()
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")

# Voice database organized by language and quality
VOICE_DATABASE = {
    "American English": {
        "code": "en-us",
        "voices": {
            "High Quality": {"female": ["af_heart", "af_bella"], "male": []},
            "Medium Quality": {
                "female": ["af_nicole", "af_aoede", "af_kore", "af_sarah"],
                "male": ["am_fenrir", "am_michael", "am_puck"],
            },
            "Low Quality": {
                "female": ["af_alloy", "af_jessica", "af_nova", "af_river", "af_sky"],
                "male": [
                    "am_adam",
                    "am_echo",
                    "am_eric",
                    "am_liam",
                    "am_onyx",
                    "am_santa",
                ],
            },
        },
    },
    "British English": {
        "code": "en-gb",
        "voices": {
            "Medium Quality": {
                "female": ["bf_alice", "bf_emma", "bf_isabella", "bf_lily"],
                "male": ["bm_daniel", "bm_fable", "bm_george", "bm_lewis"],
            }
        },
    },
    "Japanese": {
        "code": "ja",
        "voices": {
            "Medium Quality": {
                "female": ["jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro"],
                "male": ["jm_kumo"],
            }
        },
    },
    "Mandarin Chinese": {
        "code": "cmn",
        "voices": {
            "Low Quality": {
                "female": ["zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi"],
                "male": ["zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"],
            }
        },
    },
    "Spanish": {
        "code": "es",
        "voices": {
            "Medium Quality": {"female": ["ef_dora"], "male": ["em_alex", "em_santa"]}
        },
    },
    "French": {
        "code": "fr-fr",
        "voices": {"Medium Quality": {"female": ["ff_siwis"], "male": []}},
    },
    "Hindi": {
        "code": "hi",
        "voices": {
            "Medium Quality": {
                "female": ["hf_alpha", "hf_beta"],
                "male": ["hm_omega", "hm_psi"],
            }
        },
    },
    "Italian": {
        "code": "it",
        "voices": {"Medium Quality": {"female": ["if_sara"], "male": ["im_nicola"]}},
    },
    "Brazilian Portuguese": {
        "code": "pt-br",
        "voices": {
            "Medium Quality": {"female": ["pf_dora"], "male": ["pm_alex", "pm_santa"]}
        },
    },
}


def get_language_code(language_name: str) -> str:
    """Get language code from display name"""
    return VOICE_DATABASE.get(language_name, {}).get("code", "en-us")


def get_voices_for_language_and_quality(
    language_name: str,
    quality_name: str = "All Qualities",
    gender_filter: str = "All Genders",
) -> list[str]:
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


def get_available_genders_for_language(
    language_name: str, quality_name: str = "All Qualities"
) -> list[str]:
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
        title="Kokoro TTS Streaming",
    ) as ui:
        gr.Markdown("# 🎵 Kokoro TTS Streaming")
        gr.Markdown("### Multi-language Text-to-Speech with Advanced Filtering")
        gr.Markdown(
            "Filter by **language**, **quality level**, and **gender** to find the perfect voice from 149 options across 9+ languages!"
        )

        with gr.Row():
            with gr.Column(scale=2):
                with gr.Tab("Text Input"):
                    text_input = gr.TextArea(
                        label="Input Text",
                        placeholder="Enter text to convert to speech...",
                        value="Kokoro TTS streaming demo. Real-time speech synthesis!",
                        lines=4,
                    )

                with gr.Tab("File Upload"):
                    file_input = gr.File(
                        label="Upload Text/PDF File",
                        file_types=[".txt", ".md", ".rtf", ".pdf"],
                        file_count="single",
                    )
                    file_text_display = gr.TextArea(
                        label="File Content",
                        placeholder="File content will appear here...",
                        lines=4,
                        interactive=False,
                    )

                with gr.Row():
                    language_input = gr.Dropdown(
                        label="Language",
                        value="American English",
                        choices=list(VOICE_DATABASE.keys()),
                        scale=1,
                    )

                    quality_input = gr.Dropdown(
                        label="Quality Level",
                        value="All Qualities",
                        choices=get_available_qualities_for_language(
                            "American English"
                        ),
                        scale=1,
                    )

                    gender_input = gr.Dropdown(
                        label="Gender",
                        value="All Genders",
                        choices=get_available_genders_for_language(
                            "American English", "All Qualities"
                        ),
                        scale=1,
                    )

                voice_input = gr.Dropdown(
                    label="Voice",
                    value="af_sky",
                    choices=get_voices_for_language_and_quality(
                        "American English", "All Qualities", "All Genders"
                    ),
                    scale=2,
                    allow_custom_value=True,
                )

                speed_input = gr.Slider(
                    label="Speed", minimum=0.5, maximum=2.0, value=1.0, step=0.1
                )

                # Audio Format Controls
                gr.Markdown("### 🎵 Audio Format Settings")

                # Quick format recommendations
                with gr.Row():
                    quick_format_btns = []
                    for fmt, desc in [
                        ("wav", "🎵 Best Quality"),
                        ("mp3", "🎧 Most Compatible"),
                        ("flac", "🎶 Best Compression"),
                        ("m4a", "📱 Mobile Friendly"),
                    ]:
                        btn = gr.Button(desc, size="sm", scale=1)
                        quick_format_btns.append((btn, fmt))

                def set_quick_format(format_type):
                    bitrate_settings = {
                        "wav": "192k",  # Not used but for consistency
                        "mp3": "192k",  # Good balance
                        "flac": "192k",  # Not used but for consistency
                        "m4a": "192k",  # Good for mobile
                    }
                    return format_type, bitrate_settings.get(format_type, "192k")

                with gr.Row():
                    format_input = gr.Radio(
                        label="Output Format",
                        value="wav",
                        choices=[
                            ("🎵 WAV - Uncompressed (Highest Quality)", "wav"),
                            ("🎶 FLAC - Lossless (High Quality, Smaller)", "flac"),
                            ("🎧 MP3 - Lossy (Good Quality, Small)", "mp3"),
                            ("📱 M4A - Lossy (Good Quality, Mobile)", "m4a"),
                            ("🔊 OGG - Lossy (Good Quality, Open)", "ogg"),
                        ],
                        scale=3,
                    )

                with gr.Row():
                    bitrate_input = gr.Dropdown(
                        label="Audio Quality (for MP3/M4A/OGG)",
                        value="192k",
                        choices=[
                            ("96 kbps - Lower quality, smaller file", "96k"),
                            ("128 kbps - Standard quality", "128k"),
                            ("192 kbps - High quality (recommended)", "192k"),
                            ("256 kbps - Very high quality", "256k"),
                            ("320 kbps - Maximum quality", "320k"),
                        ],
                        scale=2,
                    )

                format_info = gr.Markdown(
                    value="**WAV**: Uncompressed audio, largest file size, perfect quality"
                )

                # File size estimation
                size_estimate = gr.Markdown(
                    value="📊 **Estimated file size**: ~240 KB (for 10 seconds)",
                    visible=True,
                )

                # Update format info and bitrate visibility when format changes
                def update_format_info_and_controls(format_choice, bitrate_choice):
                    format_descriptions = {
                        "wav": "**WAV**: Uncompressed audio, largest file size, perfect quality. Best for: Archival, editing",
                        "flac": "**FLAC**: Lossless compression, ~50% smaller than WAV, perfect quality. Best for: High-quality storage",
                        "mp3": "**MP3**: Lossy compression, small files, widely compatible. Best for: Sharing, streaming",
                        "m4a": "**M4A**: Lossy compression, small files, great for mobile devices. Best for: Mobile, iTunes",
                        "ogg": "**OGG**: Lossy compression, open standard, good quality. Best for: Web, open-source apps",
                    }

                    # Calculate estimated file size for 10 seconds of audio
                    if format_choice == "wav":
                        size_kb = 24000 * 2 * 10 / 1024  # 24kHz * 2 bytes * 10 seconds
                        size_info = f"📊 **Estimated size**: ~{size_kb:.0f} KB (for 10s) - Uncompressed"
                        bitrate_visible = gr.update(visible=False)
                    elif format_choice == "flac":
                        size_kb = (24000 * 2 * 10 / 1024) * 0.5  # ~50% compression
                        size_info = f"📊 **Estimated size**: ~{size_kb:.0f} KB (for 10s) - Lossless compression"
                        bitrate_visible = gr.update(visible=False)
                    else:  # Lossy formats
                        bitrate_num = int(bitrate_choice.replace("k", ""))
                        size_kb = (
                            bitrate_num * 10
                        ) / 8  # bitrate * duration / 8 bits per byte
                        size_info = f"📊 **Estimated size**: ~{size_kb:.0f} KB (for 10s) - {bitrate_num} kbps"
                        bitrate_visible = gr.update(visible=True)

                    format_desc = format_descriptions.get(
                        format_choice, "Select a format to see details"
                    )

                    return format_desc, size_info, bitrate_visible

                # Update bitrate visibility based on format
                def update_bitrate_visibility(format_choice):
                    lossy_formats = ["mp3", "m4a", "ogg"]
                    return gr.update(visible=format_choice in lossy_formats)

                format_input.change(
                    fn=lambda fmt, br: update_format_info_and_controls(fmt, br),
                    inputs=[format_input, bitrate_input],
                    outputs=[format_info, size_estimate, bitrate_input],
                )

                bitrate_input.change(
                    fn=lambda fmt, br: update_format_info_and_controls(fmt, br)[1],
                    inputs=[format_input, bitrate_input],
                    outputs=[size_estimate],
                )

                # Connect quick format buttons
                for btn, fmt in quick_format_btns:
                    btn.click(
                        fn=lambda f=fmt: set_quick_format(f),
                        outputs=[format_input, bitrate_input],
                    )

                generate_btn = gr.Button("🎤 Generate Speech", variant="primary")

            with gr.Column(scale=1):
                audio_output = gr.Audio(
                    label="Audio Preview", autoplay=True
                )
                download_output = gr.File(label="Download Audio File", visible=True)
                metrics_display = gr.Markdown(
                    value="*Generate audio to see processing metrics*", visible=True
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
            voices = get_voices_for_language_and_quality(
                language_name, quality_name, gender_name
            )
            if voices:
                return gr.update(choices=voices, value=voices[0])
            return gr.update(choices=[], value=None)

        # Handle file upload
        def handle_file_upload(file):
            logger.info("=== FILE UPLOAD FUNCTION CALLED ===")
            logger.debug(f"File upload called with: {file}")
            logger.debug(f"File type: {type(file)}")
            logger.debug(f"File repr: {repr(file)}")
            
            if file is None:
                logger.warning("No file provided to upload function")
                return ""

            try:
                # Handle different Gradio file object formats
                file_path = None
                
                # Log all attributes of the file object for debugging
                if hasattr(file, '__dict__'):
                    logger.debug(f"File object attributes: {file.__dict__}")
                else:
                    logger.debug(f"File object dir: {dir(file)}")
                
                if hasattr(file, 'name'):
                    file_path = file.name
                    logger.info(f"File object with .name attribute: {file_path}")
                elif hasattr(file, 'path'):
                    file_path = file.path
                    logger.info(f"File object with .path attribute: {file_path}")
                elif isinstance(file, str):
                    file_path = file
                    logger.info(f"File provided as string: {file_path}")
                else:
                    logger.error(f"Unknown file object type: {type(file)}")
                    logger.error(f"File object: {file}")
                    logger.error(f"File attributes: {dir(file)}")
                    return "❌ Invalid file object received"
                
                if not file_path:
                    logger.error("No file path could be extracted from file object")
                    return "❌ Could not get file path"
                    
                logger.info(f"Extracted file path: {file_path}")
                
                if not os.path.exists(file_path):
                    logger.error(f"File does not exist at path: {file_path}")
                    return "❌ File does not exist"

                # Get file info
                file_size = os.path.getsize(file_path)
                logger.info(f"Processing file: {file_path} (size: {file_size} bytes)")
                
                file_extension = file_path.lower().split(".")[-1]
                logger.debug(f"File extension: {file_extension}")
                content = ""

                if file_extension == "pdf":
                    logger.info("Processing PDF file")
                    try:
                        with open(file_path, "rb") as pdf_file:
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            text_parts = []
                            page_count = len(pdf_reader.pages)
                            logger.debug(f"PDF has {page_count} pages")

                            for page_num in range(page_count):
                                page = pdf_reader.pages[page_num]
                                page_text = page.extract_text()
                                text_parts.append(page_text)
                                logger.debug(f"Page {page_num + 1}: {len(page_text)} characters")

                            content = "\n".join(text_parts)
                            logger.info(f"PDF content extracted successfully: {len(content)} characters")

                    except Exception as pdf_error:
                        logger.exception(f"Error reading PDF: {pdf_error}")
                        return f"❌ Error reading PDF: {str(pdf_error)}"

                else:
                    logger.info(f"Processing text file with extension: {file_extension}")
                    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
                    
                    for i, encoding in enumerate(encodings):
                        try:
                            logger.debug(f"Attempting encoding {i+1}/{len(encodings)}: {encoding}")
                            with open(file_path, encoding=encoding) as f:
                                content = f.read()
                            logger.info(f"Successfully read file with {encoding}: {len(content)} characters")
                            break
                        except UnicodeDecodeError as e:
                            logger.warning(f"UnicodeDecodeError with {encoding}: {e}")
                            continue
                        except Exception as e:
                            logger.exception(f"Unexpected error with {encoding}: {e}")
                            return f"❌ Error reading text file: {str(e)}"

                if not content:
                    logger.error("No content could be extracted from file")
                    return "❌ Could not extract text from file. Please ensure it's a valid text or PDF file."

                # Limit content length for performance
                max_chars = 10000
                original_length = len(content)
                if original_length > max_chars:
                    content = content[:max_chars] + "\n\n[Content truncated - file too long]"
                    logger.warning(f"Content truncated from {original_length} to {max_chars} characters")

                logger.info(f"File processing completed successfully: {len(content)} characters")
                return content

            except Exception as e:
                logger.exception(f"Unexpected exception in file upload: {e}")
                return f"❌ Error reading file: {str(e)}"

        # Handle button click
        def handle_generate(
            text, file_content, voice, language_name, speed, output_format, bitrate
        ):
            logger.info("=== GENERATE FUNCTION CALLED ===")
            logger.debug(f"Parameters: text='{text[:50] if text else 'None'}...', voice='{voice}', language='{language_name}', speed={speed}, format={output_format}")
            
            # Simplified input handling
            input_text = ""
            if file_content and file_content.strip():
                input_text = file_content.strip()
                logger.info(f"Using file content: {len(input_text)} characters")
            elif text and text.strip():
                input_text = text.strip()
                logger.info(f"Using text input: {len(input_text)} characters")

            if not input_text:
                logger.warning("No input text provided")
                return None, None, "❌ Please enter text or upload a file"

            if not voice:
                logger.warning("No voice selected")
                return None, None, "❌ Please select a voice"

            logger.info(f"Starting audio generation - Text preview: '{input_text[:100]}{'...' if len(input_text) > 100 else ''}'")
            try:
                # Start timing
                start_time = time.time()

                language_code = get_language_code(language_name)
                logger.debug(f"Language code: {language_code}")
                
                # Use regular create method instead of streaming for Gradio compatibility
                logger.info("Calling kokoro.create() for audio generation")
                audio_data, sample_rate = kokoro.create(
                    input_text, voice=voice, speed=speed, lang=language_code
                )
                logger.info(f"Audio generated successfully: {len(audio_data)} samples at {sample_rate}Hz")

                # Calculate timing and metrics
                end_time = time.time()
                processing_time = end_time - start_time
                audio_duration = len(audio_data) / sample_rate

                # Format metrics
                metrics_text = f"""**Generation Metrics:**
- Processing Time: {processing_time:.2f} seconds
- Audio Duration: {audio_duration:.2f} seconds
- Speed Ratio: {audio_duration / processing_time:.1f}x real-time
- Sample Rate: {sample_rate:,} Hz
- Audio Samples: {len(audio_data):,}
- Output Format: {SUPPORTED_FORMATS[output_format]["name"]}"""

                logger.debug(f"Generation metrics: Processing={processing_time:.2f}s, Duration={audio_duration:.2f}s, Ratio={audio_duration/processing_time:.1f}x")

                # Handle audio conversion and download file
                download_file = None
                try:
                    logger.debug(f"Creating download file in {output_format} format")
                    if output_format.lower() == "wav":
                        # Create WAV file for download using soundfile
                        import soundfile as sf

                        with tempfile.NamedTemporaryFile(
                            suffix=".wav", delete=False
                        ) as temp_file:
                            sf.write(temp_file.name, audio_data, sample_rate)
                            download_file = temp_file.name
                            logger.info(f"WAV file created: {download_file}")
                    else:
                        # Convert to requested format and create downloadable file
                        logger.debug(f"Converting audio to {output_format} with bitrate {bitrate}")
                        converted_audio = convert_audio(
                            audio_data, sample_rate, output_format, bitrate
                        )

                        # Create temporary file for download
                        with tempfile.NamedTemporaryFile(
                            suffix=f".{output_format}", delete=False
                        ) as temp_file:
                            temp_file.write(converted_audio)
                            download_file = temp_file.name
                            logger.info(f"Converted {output_format} file created: {download_file}")
                except Exception as e:
                    logger.exception(f"Audio conversion error: {e}")
                    metrics_text += f"\n- Conversion Error: {str(e)}"

                logger.info(f"Generation completed successfully. Download file: {download_file}")
                return (sample_rate, audio_data), download_file, metrics_text

            except Exception as e:
                logger.exception(f"Exception in audio generation: {e}")
                error_msg = f"❌ Error generating audio: {str(e)}"
                return None, None, error_msg

        # Update quality dropdown when language changes
        language_input.change(
            fn=update_quality_choices, inputs=[language_input], outputs=[quality_input]
        )

        # Update gender dropdown when language or quality changes
        language_input.change(
            fn=update_gender_choices,
            inputs=[language_input, quality_input],
            outputs=[gender_input],
        )

        quality_input.change(
            fn=update_gender_choices,
            inputs=[language_input, quality_input],
            outputs=[gender_input],
        )

        # Update voice dropdown when language, quality, or gender changes
        language_input.change(
            fn=update_voice_choices,
            inputs=[language_input, quality_input, gender_input],
            outputs=[voice_input],
        )

        quality_input.change(
            fn=update_voice_choices,
            inputs=[language_input, quality_input, gender_input],
            outputs=[voice_input],
        )

        gender_input.change(
            fn=update_voice_choices,
            inputs=[language_input, quality_input, gender_input],
            outputs=[voice_input],
        )

        # Connect file upload to display content
        file_input.change(
            fn=handle_file_upload, inputs=[file_input], outputs=[file_text_display]
        )

        generate_btn.click(
            fn=handle_generate,
            inputs=[
                text_input,
                file_text_display,
                voice_input,
                language_input,
                speed_input,
                format_input,
                bitrate_input,
            ],
            outputs=[audio_output, download_output, metrics_display],
            show_progress=True,
        )

        # Add format information
        gr.Markdown("""
        ### 🎵 Audio Format Information:
        - **WAV**: Uncompressed, highest quality, larger file size
        - **FLAC**: Lossless compression, high quality, moderate file size  
        - **MP3**: Lossy compression, good quality, small file size
        - **M4A/AAC**: Lossy compression, good quality, small file size
        - **OGG**: Lossy compression, good quality, small file size
        
        *Bitrate setting only affects lossy formats (MP3, M4A, OGG)*
        """)

        # Add example texts in multiple languages with human readable names
        gr.Examples(
            examples=[
                [
                    "Hello, this is a test of Kokoro TTS streaming capabilities.",
                    "af_sky",
                    "American English",
                    "Low Quality",
                    "Female",
                    1.0,
                    "wav",
                    "128k",
                ],
                [
                    "The quick brown fox jumps over the lazy dog.",
                    "af_bella",
                    "American English",
                    "High Quality",
                    "Female",
                    1.2,
                    "mp3",
                    "192k",
                ],
                [
                    "Welcome to the future of text-to-speech technology!",
                    "af_sarah",
                    "American English",
                    "Medium Quality",
                    "Female",
                    0.9,
                    "flac",
                    "128k",
                ],
                [
                    "Good morning! How are you today?",
                    "bf_alice",
                    "British English",
                    "Medium Quality",
                    "Female",
                    1.0,
                    "m4a",
                    "128k",
                ],
                [
                    "こんにちは、元気ですか？",
                    "jf_alpha",
                    "Japanese",
                    "Medium Quality",
                    "Female",
                    1.0,
                    "ogg",
                    "192k",
                ],
                [
                    "Bonjour, comment allez-vous?",
                    "ff_siwis",
                    "French",
                    "Medium Quality",
                    "Female",
                    1.0,
                    "wav",
                    "128k",
                ],
            ],
            inputs=[
                text_input,
                voice_input,
                language_input,
                quality_input,
                gender_input,
                speed_input,
                format_input,
                bitrate_input,
            ],
        )

    return ui


def main():
    """Main entry point for the Kokoro TTS application."""
    logger.info("=== KOKORO TTS APPLICATION STARTING ===")
    
    app = create_streaming_app()
    
    # Read configuration from environment variables (loaded from .env)
    headless = os.getenv("KOKORO_HEADLESS", "false").lower() == "true"
    debug_mode = os.getenv("KOKORO_DEBUG", "true").lower() == "true"
    server_port = int(os.getenv("KOKORO_PORT", "7860"))
    server_host = os.getenv("KOKORO_HOST", "127.0.0.1")
    launch_browser = os.getenv("KOKORO_LAUNCH_BROWSER", "true").lower() == "true"
    
    # Log all configuration values
    logger.info("Application configuration:")
    logger.info(f"  KOKORO_HEADLESS: {headless}")
    logger.info(f"  KOKORO_DEBUG: {debug_mode}")
    logger.info(f"  KOKORO_HOST: {server_host}")
    logger.info(f"  KOKORO_PORT: {server_port}")
    logger.info(f"  KOKORO_LAUNCH_BROWSER: {launch_browser}")
    logger.info(f"  LOG_LEVEL: {os.getenv('LOG_LEVEL', 'DEBUG')}")
    
    if headless:
        logger.info("Starting in headless mode")
        # Headless mode - no browser launch
        app.launch(
            debug=debug_mode,
            share=False,
            server_name=server_host,
            server_port=server_port,
            inbrowser=False,
            show_error=True
        )
    else:
        logger.info("Starting in normal mode with browser")
        # Normal mode - launch browser
        inbrowser = launch_browser
        app.launch(
            debug=debug_mode, 
            share=False, 
            server_name=server_host, 
            server_port=server_port,
            inbrowser=inbrowser
        )


if __name__ == "__main__":
    main()
