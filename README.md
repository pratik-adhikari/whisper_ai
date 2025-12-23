# ytx - YouTube Transcription Tool

**Self-contained Docker-based CLI** for transcribing YouTube videos using [whisper.cpp](https://github.com/ggml-org/whisper.cpp) with CUDA acceleration.

## Features

✅ **Zero host dependencies** - Everything runs in Docker (yt-dlp, whisper, ffmpeg)  
✅ **One-command transcription** - Just run `./ytx.sh "<url>"` and get transcripts  
✅ **CUDA acceleration** - Uses GPU for fast transcription  
✅ **Multiple formats** - Outputs `.txt`, `.srt`, `.vtt`, and `.json`  
✅ **Organized outputs** - Each video gets its own dated folder with metadata  
✅ **Devanagari support** - Optional transliteration for Hindi/Sanskrit content  
✅ **Caption merging** - Combine short captions into full sentences  
✅ **Metadata tracking** - Saves video info, model used, timestamps, etc.  
✅ **Client-ready** - Ship Docker image to clients without worrying about dependencies  

## Quick Start

```bash
# 1. Build Docker image (first time only, ~5-10 minutes)
docker build -f Dockerfile.whispercpp -t whispercpp:cuda12 .

# 2. Download a model
mkdir -p models
docker run --rm --entrypoint bash \
  -v $PWD/models:/models whispercpp:cuda12 \
  -c 'cd /opt/whisper_models_scripts && ./download-ggml-model.sh base && mv -f ggml-base.bin /models/'

# 3. Transcribe a video
./ytx.sh "https://www.youtube.com/watch?v=VIDEO_ID"
```

Output will be in `./out/YYYY-MM-DD__video-title__VIDEO_ID/`

## Installation

### Prerequisites

**On host system (minimal):**
- Docker with NVIDIA GPU support
- NVIDIA GPU with CUDA 12.2+ support
- Python 3.8+ (standard library only - no packages required!)

**In Docker container (automatic):**
- yt-dlp with deno runtime
- whisper.cpp with CUDA
- ffmpeg
- indic-transliteration (for Devanagari)
- All other dependencies

### Setup

```bash
# Clone repository
git clone https://github.com/pratik-adhikari/whisper_ai.git
cd whisper_ai

# Make wrapper script executable
chmod +x ytx.sh

# Build Docker image (first time only, ~5-10 minutes)
docker build -f Dockerfile.whispercpp -t whispercpp:cuda12 .

# That's it! No pip install needed on host.
```

## Examples

See [examples/bhagavad_gita_chapter3](examples/bhagavad_gita_chapter3/) for real output from transcribing a Sanskrit chanting video with Devanagari transliteration. Includes:
- Complete metadata (`meta.json`)
- Roman transliteration excerpts
- Devanagari (देवनागरी) transliteration excerpts
- SRT subtitle format samples

This demonstrates the tool's quality on religious/spiritual content in Sanskrit.

## Usage

### Basic Usage

```bash
./ytx.sh "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Options

```bash
./ytx.sh "<url>" [OPTIONS]

Required:
  url                   YouTube video URL

Model Options:
  --model MODEL         Whisper model: base, medium, large-v3 (default: large-v3)
  --lang LANG           Language code (en, hi, de, etc.) or 'auto' (default: auto)
  --threads N           Number of CPU threads (default: 8)

Output Options:
  --out-root DIR        Output root directory (default: ./out)
  --force               Overwrite existing output folder

Post-Processing:
  --devanagari          Transliterate to Devanagari (creates .dev.* files)
  --merge-captions      Merge captions into sentences (creates .merged.* files)

Docker Options:
  --image NAME          Docker image name (default: whispercpp:cuda12)
  --pull                Force rebuild Docker image

Other:
  --verbose             Show detailed output
  --version             Show version
```

### Examples

**Transcribe with default settings:**
```bash
./ytx.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Use faster base model:**
```bash
./ytx.sh "<url>" --model base
```

**Hindi video with Devanagari output:**
```bash
./ytx.sh "<url>" --lang hi --devanagari
```

**Merge short captions into sentences:**
```bash
./ytx.sh "<url>" --merge-captions
```

**All features enabled:**
```bash
./ytx.sh "<url>" --model large-v3 --devanagari --merge-captions
```

**Force overwrite existing output:**
```bash
./ytx.sh "<url>" --force
```

## Output Structure

Each transcription creates a folder: `YYYY-MM-DD__<title>__<video-id>/`

```
out/
└── 2025-12-23__never-gonna-give-you-up__dQw4w9WgXcQ/
    ├── meta.json              # Video metadata and transcription info
    ├── audio.m4a              # Original downloaded audio
    ├── transcript.txt         # Plain text transcript
    ├── transcript.srt         # SubRip subtitles
    ├── transcript.vtt         # WebVTT subtitles
    ├── transcript.json        # JSON with timestamps
    ├── transcript.dev.txt     # (if --devanagari) Devanagari text
    ├── transcript.dev.srt     # (if --devanagari) Devanagari SRT
    ├── transcript.dev.vtt     # (if --devanagari) Devanagari VTT
    ├── transcript.merged.txt  # (if --merge-captions) Merged text
    ├── transcript.merged.srt  # (if --merge-captions) Merged SRT
    └── transcript.merged.vtt  # (if --merge-captions) Merged VTT
```

### meta.json

Contains:
- `run_date` - When transcription was run
- `url` - Original video URL
- `video_id` - YouTube video ID
- `title` - Video title
- `channel` - Channel name
- `upload_date` - When video was uploaded
- `duration` - Video duration (seconds)
- `webpage_url` - Full webpage URL
- `model` - Whisper model used
- `lang_mode` - Language mode used
- `gpu_used` - Whether GPU was used
- `tool_version` - Tool version

## Models

Download models before use:

```bash
# Base model (fast, ~150MB)
mkdir -p models
docker run --rm --entrypoint bash \
  -v $PWD/models:/models whispercpp:cuda12 \
  -c 'cd /opt/whisper_models_scripts && ./download-ggml-model.sh base && mv -f ggml-base.bin /models/'

# Medium model (balanced, ~1.5GB)
docker run --rm --entrypoint bash \
  -v $PWD/models:/models whispercpp:cuda12 \
  -c 'cd /opt/whisper_models_scripts && ./download-ggml-model.sh medium && mv -f ggml-medium.bin /models/'

# Large-v3 model (best quality, ~3GB)
docker run --rm --entrypoint bash \
  -v $PWD/models:/models whispercpp:cuda12 \
  -c 'cd /opt/whisper_models_scripts && ./download-ggml-model.sh large-v3 && mv -f ggml-large-v3.bin /models/'
```

## Troubleshooting

### yt-dlp HTTP 403 Errors

The Dockerfile includes `deno` for JavaScript execution, which handles most video sites. If you still get 403 errors, the video may require authentication or may not be available.

## Deploying to Client Systems

This tool is designed for easy deployment to client systems:

**1. Export Docker Image:**
```bash
# Save image to file
docker save whispercpp:cuda12 | gzip > whispercpp-cuda12.tar.gz

# Transfer to client (scp, USB drive, etc.)
```

**2. On Client System:**
```bash
# Load image
docker load < whispercpp-cuda12.tar.gz

# Download models
mkdir -p models
docker run --rm --entrypoint bash \
  -v $PWD/models:/models whispercpp:cuda12 \
  -c 'cd /opt/whisper_models_scripts && ./download-ggml-model.sh base && mv -f ggml-base.bin /models/'

# Run transcriptions
./ytx.sh "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Requirements on client:**
- Docker with NVIDIA GPU support
- Python 3 (standard library only)
- That's it!

## Troubleshooting

### Missing Model Error

Download the model first (see Models section above).

### GPU Not Detected

Ensure:
1. NVIDIA drivers are installed
2. Docker has GPU support: `docker run --rm --gpus all nvidia/cuda:12.2.2-base-ubuntu22.04 nvidia-smi`
3. You're using the `--gpus all` flag (automatically added by ytx)

### Docker Build Fails

**CUDA Architecture**: If you don't have an RTX 4070, edit `Dockerfile.whispercpp` line 24:
```dockerfile
# RTX 3000 series
-DCMAKE_CUDA_ARCHITECTURES=86

# RTX 4000 series  
-DCMAKE_CUDA_ARCHITECTURES=89

# A100/H100
-DCMAKE_CUDA_ARCHITECTURES=80
```

**Build Time**: First build takes 5-10 minutes to compile whisper.cpp.

### Output Folder Already Exists

Use `--force` to overwrite:
```bash
./ytx.sh "<url>" --force
```

### Devanagari Not Working

Install the Python library:
```bash
pip install indic-transliteration
```

## Advanced Usage

### Using Python Module Directly

```bash
# Instead of ./ytx.sh, use:
python3 -m ytx "https://www.youtube.com/watch?v=VIDEO_ID" --model base
```

### Custom Output Location

```bash
./ytx.sh "<url>" --out-root /mnt/external/transcripts
```

### Rebuilding Docker Image

```bash
./ytx.sh "<url>" --pull
# or manually:
docker build -f Dockerfile.whispercpp -t whispercpp:cuda12 .
```

### Processing Multiple Videos

```bash
# Create a simple loop
for url in $(cat urls.txt); do
  ./ytx.sh "$url" --model base || echo "Failed: $url"
done
```

## Development

### Project Structure

```
.
├── ytx/                      # Python package
│   ├── __init__.py          # Package init with version
│   ├── __main__.py          # CLI entry point
│   ├── metadata.py          # Video metadata fetching
│   └── docker_manager.py    # Docker operations
├── image/
│   └── transcribe_url.sh    # Container-side script
├── scripts/
│   └── postprocess.py       # Caption merging & transliteration
├── ytx.sh                   # Executable wrapper script
├── Dockerfile.whispercpp    # Multi-stage Docker build
├── pyproject.toml           # Python package config
├── .gitignore               # Git ignore rules
├── .dockerignore            # Docker ignore rules
└── README.md                # This file
```

### Environment Variables for Container

When running the container directly:

```bash
docker run --rm --gpus all \
  -v $PWD/out/test:/out \
  -v $PWD/models/ggml-base.bin:/model:ro \
  -e MODEL=/model \
  -e LANG=auto \
  -e THREADS=8 \
  whispercpp:cuda12 \
  "https://www.youtube.com/watch?v=VIDEO_ID"
```

## License

MIT License - See LICENSE file

## Credits

- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) - Fast C++ implementation of Whisper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [indic-transliteration](https://github.com/sanskrit-coders/indic_transliteration_py) - Devanagari transliteration
