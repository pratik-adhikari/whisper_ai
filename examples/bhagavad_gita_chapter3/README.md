# Example Output: Bhagavad Gita Chapter 3

This directory contains example output from transcribing a Sanskrit chanting video (Bhagavad Gita Chapter 3).

**Source Video:** [Chapter 3 Full Bhagavad-Gītā Chanting](https://www.youtube.com/watch?v=8HLAEXo0Tr0)  
**Channel:** Kuldeep M Pai  
**Duration:** 12 minutes 36 seconds  
**Language:** Sanskrit

## Command Used

```bash
./ytx.sh "https://www.youtube.com/watch?v=8HLAEXo0Tr0" --devanagari
```

## Files Included

### 1. `meta.json`
Complete metadata about the transcription including:
- Video information (title, channel, upload date, duration)
- Transcription settings (model, language mode, GPU usage)
- Tool version and run date

### 2. `transcript_excerpt.txt`
First 50 lines of the Roman transliteration transcript showing:
- Clean, plain text format
- Sanskrit text in Roman script
- One line per caption segment

### 3. `transcript_devanagari_excerpt.txt`
First 50 lines of the Devanagari transliteration showing:
- Same content as Roman version
- **Automatically converted to Devanagari script (देवनागरी)**
- Uses `indic-transliteration` with multi-scheme fallback

### 4. `transcript_excerpt.srt`
First 30 caption blocks in SubRip format showing:
- Industry-standard subtitle format
- Precise timestamps
- Roman transliteration

### 5. `transcript_devanagari_excerpt.srt`
First 30 caption blocks in Devanagari script showing:
- **SRT format with Devanagari text**
- Same timestamps as Roman version
- Ready for video subtitles in native script

## Full Output Structure

When you run the tool, you get a complete folder like:
```
2025-12-23__chapter_3_full_bhagavad_gt_chanting__8HLAEXo0Tr0/
├── meta.json                      # Video & transcription metadata
├── audio.opus                     # Original downloaded audio
├── transcript.txt                 # Plain text (Roman)
├── transcript.srt                 # SubRip subtitles (Roman)
├── transcript.vtt                 # WebVTT subtitles (Roman)
├── transcript.json                # JSON with timestamps
├── transcript.dev.txt             # Plain text (Devanagari)
├── transcript.dev.srt             # SubRip subtitles (Devanagari)
└── transcript.dev.vtt             # WebVTT subtitles (Devanagari)
```

## Quality Notes

The transcription quality for Sanskrit chanting is excellent because:
- **whisper.cpp** handles phonetic consistency well
- The `large-v3` model was used (most accurate)
- GPU acceleration (CUDA) enabled
- Devanagari transliteration uses multiple schemes (ITRANS, HK, IAST) for best results

## Use Cases

This example demonstrates:
1. ✅ **Religious/Spiritual Content** - Sanskrit chants, mantras, prayers
2. ✅ **Educational Content** - Language learning, pronunciation guides
3. ✅ **Accessibility** - Providing both Roman and native script subtitles
4. ✅ **Archival** - Preserving oral traditions in written form
