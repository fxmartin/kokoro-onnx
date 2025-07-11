# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

kokoro-onnx is a TTS (Text-to-Speech) library using ONNX Runtime based on Kokoro-TTS. The library supports multiple languages, voices, and provides near real-time performance on Apple Silicon.

## Common Development Commands

### Development Setup
```bash
# Install uv (recommended package manager)
pip install uv

# Install dependencies with dev group
uv sync --group dev

# Install with GPU support (Windows/Linux x86_64 only)
uv add kokoro-onnx[gpu]
```

### Code Quality
```bash
# Format code
uv run ruff format

# Check linting 
uv run ruff check

# Apply safe fixes
uv run ruff check --fix
```

### Building and Publishing
```bash
# Build package
rm -rf dist
uv build

# Publish (requires UV_PUBLISH_TOKEN)
UV_PUBLISH_TOKEN="token" uv publish
```

### Testing Examples
```bash
# Basic usage example
uv run examples/save.py

# Run with debug logging
LOG_LEVEL=DEBUG uv run examples/save.py

# Test different features
uv run examples/with_cuda.py      # GPU acceleration
uv run examples/with_stream.py    # Streaming audio
uv run examples/with_voice.py     # Different voices
```

## Architecture

### Core Components

- **`src/kokoro_onnx/__init__.py`**: Main `Kokoro` class that handles TTS generation
- **`src/kokoro_onnx/config.py`**: Configuration classes (`KoKoroConfig`, `EspeakConfig`) and constants
- **`src/kokoro_onnx/tokenizer.py`**: Phoneme tokenization using espeak
- **`src/kokoro_onnx/trim.py`**: Audio trimming utilities
- **`src/kokoro_onnx/log.py`**: Logging configuration

### Key Design Patterns

1. **Model Loading**: Uses ONNX Runtime with automatic provider selection (CPU/GPU)
2. **Voice Management**: Voice styles loaded from `.bin` files as numpy arrays
3. **Phoneme Processing**: Text converted to phonemes via espeak, then tokenized
4. **Batching**: Long text automatically split into chunks of `MAX_PHONEME_LENGTH` (510)
5. **Streaming**: Async generator pattern for real-time audio generation

### Provider Selection Priority
1. Environment variable `ONNX_PROVIDER` if set
2. GPU providers if `onnxruntime-gpu` installed 
3. Default to `CPUExecutionProvider`

### Audio Pipeline
Text → Phonemes (espeak) → Tokens → ONNX Model → Audio (24kHz) → Optional Trimming

## Model Files

Download required model files:
```bash
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

## Configuration

- **Sample Rate**: 24000 Hz (fixed)
- **Max Phoneme Length**: 510 tokens per batch
- **Speed Range**: 0.5 - 2.0
- **Supported Languages**: Multi-language via espeak phonemization

## Examples Structure

The `examples/` directory contains comprehensive usage examples:
- Language-specific examples (`chinese.py`, `english.py`, etc.)
- Feature demonstrations (`with_cuda.py`, `with_stream.py`, etc.)
- Integration patterns (`app.py`, `podcast.py`)