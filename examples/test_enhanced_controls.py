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
Test the enhanced audio format controls UI without running full app.

Run with:
uv run examples/test_enhanced_controls.py
"""

import gradio as gr
from kokoro_onnx.convert import SUPPORTED_FORMATS, BITRATE_OPTIONS

def test_format_controls():
    """Test just the enhanced format controls UI"""
    
    with gr.Blocks(title="Audio Format Controls Test") as demo:
        gr.Markdown("# 🎵 Enhanced Audio Format Controls Test")
        
        # Audio Format Controls
        gr.Markdown("### 🎵 Audio Format Settings")
        
        # Quick format recommendations
        with gr.Row():
            quick_format_btns = []
            for fmt, desc in [
                ("wav", "🎵 Best Quality"),
                ("mp3", "🎧 Most Compatible"), 
                ("flac", "🎶 Best Compression"),
                ("m4a", "📱 Mobile Friendly")
            ]:
                btn = gr.Button(desc, size="sm", scale=1)
                quick_format_btns.append((btn, fmt))
        
        def set_quick_format(format_type):
            bitrate_settings = {
                "wav": "192k",
                "mp3": "192k", 
                "flac": "192k",
                "m4a": "192k"
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
                    ("🔊 OGG - Lossy (Good Quality, Open)", "ogg")
                ],
                scale=3
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
                    ("320 kbps - Maximum quality", "320k")
                ],
                scale=2
            )
            
        
        format_info = gr.Markdown(
            value="**WAV**: Uncompressed audio, largest file size, perfect quality"
        )
        
        # File size estimation
        size_estimate = gr.Markdown(
            value="📊 **Estimated file size**: ~240 KB (for 10 seconds)",
            visible=True
        )
        
        # Update format info and bitrate visibility when format changes
        def update_format_info_and_controls(format_choice, bitrate_choice):
            format_descriptions = {
                "wav": "**WAV**: Uncompressed audio, largest file size, perfect quality. Best for: Archival, editing",
                "flac": "**FLAC**: Lossless compression, ~50% smaller than WAV, perfect quality. Best for: High-quality storage", 
                "mp3": "**MP3**: Lossy compression, small files, widely compatible. Best for: Sharing, streaming",
                "m4a": "**M4A**: Lossy compression, small files, great for mobile devices. Best for: Mobile, iTunes",
                "ogg": "**OGG**: Lossy compression, open standard, good quality. Best for: Web, open-source apps"
            }
            
            # Calculate estimated file size for 10 seconds of audio
            if format_choice == "wav":
                size_kb = 24000 * 2 * 10 / 1024
                size_info = f"📊 **Estimated size**: ~{size_kb:.0f} KB (for 10s) - Uncompressed"
                bitrate_visible = gr.update(visible=False)
            elif format_choice == "flac":
                size_kb = (24000 * 2 * 10 / 1024) * 0.5
                size_info = f"📊 **Estimated size**: ~{size_kb:.0f} KB (for 10s) - Lossless compression"
                bitrate_visible = gr.update(visible=False)
            else:  # Lossy formats
                bitrate_num = int(bitrate_choice.replace('k', ''))
                size_kb = (bitrate_num * 10) / 8
                size_info = f"📊 **Estimated size**: ~{size_kb:.0f} KB (for 10s) - {bitrate_num} kbps"
                bitrate_visible = gr.update(visible=True)
            
            format_desc = format_descriptions.get(format_choice, "Select a format to see details")
            
            return format_desc, size_info, bitrate_visible
        
        format_input.change(
            fn=lambda fmt, br: update_format_info_and_controls(fmt, br),
            inputs=[format_input, bitrate_input],
            outputs=[format_info, size_estimate, bitrate_input]
        )
        
        bitrate_input.change(
            fn=lambda fmt, br: update_format_info_and_controls(fmt, br)[1],
            inputs=[format_input, bitrate_input],
            outputs=[size_estimate]
        )
        
        # Connect quick format buttons
        for btn, fmt in quick_format_btns:
            btn.click(
                fn=lambda f=fmt: set_quick_format(f),
                outputs=[format_input, bitrate_input]
            )
        
        # Test output display
        test_output = gr.Markdown("Click buttons and change formats to test the controls!")
        
        def show_current_selection(fmt, bitrate):
            return f"**Current Selection**: {fmt.upper()} format with {bitrate} bitrate"
        
        format_input.change(
            fn=show_current_selection,
            inputs=[format_input, bitrate_input],
            outputs=[test_output]
        )
        
        bitrate_input.change(
            fn=show_current_selection,
            inputs=[format_input, bitrate_input],
            outputs=[test_output]
        )
    
    return demo

if __name__ == "__main__":
    demo = test_format_controls()
    demo.launch(debug=True, show_error=True)