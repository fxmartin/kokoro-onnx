# Text To Speech App using Kokoro ONNX Configuration Guide

This document explains how to configure Text To Speech App using Kokoro ONNX with the `.env` file.

## Quick Start

1. **Copy the example configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** to customize your settings:
   ```bash
   nano .env
   ```

3. **Restart the application** to apply changes.

## Configuration Options

### Logging Configuration

| Variable | Description | Values | Default |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Controls verbosity of logging | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `DEBUG` |

- **DEBUG**: Most verbose - shows all internal operations
- **INFO**: Standard logging - shows important events
- **WARNING**: Only warnings and errors
- **ERROR**: Only error messages

### Server Configuration

| Variable | Description | Values | Default |
|----------|-------------|---------|---------|
| `KOKORO_HEADLESS` | Run without opening browser | `true`, `false` | `false` |
| `KOKORO_DEBUG` | Enable Gradio debug mode | `true`, `false` | `false` |
| `KOKORO_HOST` | Server bind address | IP address | `127.0.0.1` |
| `KOKORO_PORT` | Server port number | Port number | `7860` |
| `KOKORO_LAUNCH_BROWSER` | Auto-launch browser | `true`, `false` | `true` |

### Host Configuration Examples

- **Localhost only**: `KOKORO_HOST=127.0.0.1` (default, most secure)
- **All interfaces**: `KOKORO_HOST=0.0.0.0` (allows external access)
- **Specific interface**: `KOKORO_HOST=192.168.1.100`

## Example Configurations

### Development Setup
```env
LOG_LEVEL=DEBUG
KOKORO_HEADLESS=false
KOKORO_DEBUG=true
KOKORO_HOST=127.0.0.1
KOKORO_PORT=7860
KOKORO_LAUNCH_BROWSER=true
```

### Production/Server Setup
```env
LOG_LEVEL=INFO
KOKORO_HEADLESS=true
KOKORO_DEBUG=false
KOKORO_HOST=0.0.0.0
KOKORO_PORT=8080
KOKORO_LAUNCH_BROWSER=false
```

### Quiet Mode
```env
LOG_LEVEL=WARNING
KOKORO_HEADLESS=true
KOKORO_DEBUG=false
KOKORO_HOST=127.0.0.1
KOKORO_PORT=7860
KOKORO_LAUNCH_BROWSER=false
```

## Priority Order

Configuration values are loaded in this order (highest to lowest priority):

1. **Environment variables** set in shell
2. **`.env` file** values
3. **Default values** in code

This allows you to override `.env` settings temporarily:

```bash
# Override LOG_LEVEL just for this run
LOG_LEVEL=ERROR python main.py
```

## Security Notes

- The `.env` file is automatically ignored by git (in `.gitignore`)
- Never commit sensitive configuration to version control
- Use `127.0.0.1` instead of `0.0.0.0` unless you need external access
- Consider using a reverse proxy for production deployments

## Troubleshooting

### Configuration Not Loading
1. Ensure `.env` file is in the same directory as `main.py`
2. Check file permissions: `chmod 644 .env`
3. Verify no spaces around `=` in assignments: `LOG_LEVEL=DEBUG` ✓, `LOG_LEVEL = DEBUG` ✗

### Invalid Values
- Invalid `LOG_LEVEL` values default to `DEBUG`
- Invalid port numbers will cause startup errors
- Invalid boolean values default to `false`

### Checking Current Configuration
The application logs all configuration values at startup:
```
2025-07-11 15:03:52,079 - kokoro_app - INFO - Application configuration:
2025-07-11 15:03:52,079 - kokoro_app - INFO -   KOKORO_HEADLESS: False
2025-07-11 15:03:52,079 - kokoro_app - INFO -   LOG_LEVEL: DEBUG
```