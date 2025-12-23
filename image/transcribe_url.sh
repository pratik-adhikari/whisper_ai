#!/usr/bin/env bash
# Container-side script for transcribing YouTube videos with whisper.cpp

set -euo pipefail

# Parse arguments
URL="${1:-}"
if [[ -z "$URL" ]]; then
  echo "ERROR: URL required as first argument" >&2
  echo "Usage: transcribe_url.sh <youtube_url>" >&2
  exit 2
fi

# Environment variables with defaults
MODEL="${MODEL:-/models/ggml-base.bin}"
OUTDIR="${OUTDIR:-/out}"
LANG="${LANG:-auto}"
THREADS="${THREADS:-8}"
NGL="${NGL:-999}"

# Working directories
WORKDIR="/tmp/work"
mkdir -p "$OUTDIR" "$WORKDIR"

echo "========================================="
echo "YouTube Video Transcription"
echo "========================================="
echo "URL:     $URL"
echo "Model:   $MODEL"
echo "Output:  $OUTDIR"
echo "Lang:    $LANG"
echo "Threads: $THREADS"
echo "========================================="

# Step 1: Fetch video metadata
echo ""
echo "[1/5] Fetching video metadata..."
yt-dlp --dump-single-json --no-playlist "$URL" > "$WORKDIR/metadata.json"

if [[ ! -s "$WORKDIR/metadata.json" ]]; then
  echo "ERROR: Failed to fetch metadata" >&2
  exit 1
fi

echo "✓ Metadata fetched"

# Step 2: Download audio
echo ""
echo "[2/5] Downloading audio..."
yt-dlp \
  --no-playlist \
  -f "bestaudio/best" \
  --extract-audio \
  --audio-format "best" \
  --audio-quality 0 \
  -o "$WORKDIR/input.%(ext)s" \
  "$URL"

# Find downloaded audio file
AUDIO=""
for ext in m4a webm opus mp3 aac wav; do
  if [[ -f "$WORKDIR/input.${ext}" ]]; then
    AUDIO="$WORKDIR/input.${ext}"
    echo "✓ Downloaded: $AUDIO"
    break
  fi
done

if [[ -z "$AUDIO" ]]; then
  echo "ERROR: Could not find downloaded audio in $WORKDIR" >&2
  ls -lah "$WORKDIR" >&2
  exit 1
fi

# Get original extension for later
AUDIO_EXT="${AUDIO##*.}"

# Check if model exists
if [[ ! -f "$MODEL" ]]; then
  echo "ERROR: Model not found: $MODEL" >&2
  echo "" >&2
  echo "Available models:" >&2
  ls -lh /models 2>/dev/null || echo "  (none)" >&2
  echo "" >&2
  echo "Download a model first. See README for instructions." >&2
  exit 1
fi

# Step 3: Convert to WAV for whisper-cli
echo ""
echo "[3/5] Converting to 16kHz mono WAV..."
WAV="$WORKDIR/input.wav"
ffmpeg -y -hide_banner -loglevel error \
  -i "$AUDIO" \
  -ac 1 -ar 16000 -c:a pcm_s16le \
  "$WAV"

if [[ ! -s "$WAV" ]]; then
  echo "ERROR: WAV conversion failed; file missing or empty: $WAV" >&2
  ls -lah "$WORKDIR" >&2
  exit 1
fi

echo "✓ Converted: $WAV"

# Step 4: Transcribe with whisper-cli
echo ""
echo "[4/5] Transcribing with whisper.cpp..."

# Language arguments
EXTRA_LANG=()
if [[ "$LANG" != "auto" ]]; then
  EXTRA_LANG=( -l "$LANG" )
fi

# GPU offload arguments (check if -ngl is supported)
EXTRA_GPU=()
if whisper-cli -h 2>&1 | grep -q -- "-ngl"; then
  EXTRA_GPU=( -ngl "$NGL" )
  echo "  GPU offload enabled (ngl=$NGL)"
fi

# Run whisper-cli
whisper-cli \
  -m "$MODEL" \
  -f "$WAV" \
  -of "$OUTDIR/transcript" \
  -otxt -osrt -ovtt -oj \
  -t "$THREADS" \
  "${EXTRA_GPU[@]}" \
  "${EXTRA_LANG[@]}"

echo "✓ Transcription complete"

# Step 5: Save metadata and finalize outputs
echo ""
echo "[5/5] Finalizing outputs..."

# Copy original audio to output folder
cp "$AUDIO" "$OUTDIR/audio.$AUDIO_EXT"
echo "✓ Saved original audio: audio.$AUDIO_EXT"

# Copy metadata to output folder
cp "$WORKDIR/metadata.json" "$OUTDIR/metadata.json"
echo "✓ Saved metadata: metadata.json"

# Delete WAV file (we don't need it anymore)
rm -f "$WAV"

# Show final output files
echo ""
echo "========================================="
echo "Output files:"
echo "========================================="
ls -lh "$OUTDIR" | tail -n +2
echo "========================================="
echo "✓ Done!"
