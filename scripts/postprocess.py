#!/usr/bin/env python3
"""Post-processing script for caption merging and Devanagari transliteration."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple


def parse_srt_timestamp(ts: str) -> float:
    """Parse SRT timestamp to seconds.
    
    Args:
        ts: Timestamp string in format HH:MM:SS,mmm
        
    Returns:
        Time in seconds as float
    """
    # Format: HH:MM:SS,mmm
    time_part, ms_part = ts.split(',')
    h, m, s = map(int, time_part.split(':'))
    ms = int(ms_part)
    return h * 3600 + m * 60 + s + ms / 1000.0


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Timestamp string in format HH:MM:SS,mmm
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_vtt_timestamp(seconds: float) -> str:
    """Format seconds to VTT timestamp.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Timestamp string in format HH:MM:SS.mmm
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def parse_srt_file(srt_path: Path) -> List[Dict[str, Any]]:
    """Parse SRT file into segments.
    
    Args:
        srt_path: Path to SRT file
        
    Returns:
        List of segment dictionaries with 'start', 'end', 'text'
    """
    segments = []
    
    with srt_path.open('r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by double newline to get individual subtitle blocks
    blocks = re.split(r'\n\n+', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # Line 0: sequence number
        # Line 1: timestamps
        # Lines 2+: text
        timestamp_line = lines[1]
        text = '\n'.join(lines[2:])
        
        # Parse timestamps: "00:00:00,000 --> 00:00:01,000"
        match = re.match(r'(\S+)\s+-->\s+(\S+)', timestamp_line)
        if not match:
            continue
        
        start_ts, end_ts = match.groups()
        start = parse_srt_timestamp(start_ts)
        end = parse_srt_timestamp(end_ts)
        
        segments.append({
            'start': start,
            'end': end,
            'text': text
        })
    
    return segments


def merge_captions(
    segments: List[Dict[str, Any]],
    max_chars: int = 140,
    max_gap: float = 1.0
) -> List[Dict[str, Any]]:
    """Merge adjacent caption segments into full sentences.
    
    Args:
        segments: List of caption segments
        max_chars: Maximum characters before forcing a break
        max_gap: Maximum time gap (seconds) before forcing a break
        
    Returns:
        List of merged segments
    """
    if not segments:
        return []
    
    merged = []
    current = {
        'start': segments[0]['start'],
        'end': segments[0]['end'],
        'text': segments[0]['text'].strip()
    }
    
    for i in range(1, len(segments)):
        seg = segments[i]
        text = seg['text'].strip()
        
        # Check if we should merge
        gap = seg['start'] - current['end']
        combined_text = current['text'] + ' ' + text
        
        # Check terminal punctuation in current text
        has_terminal = current['text'].rstrip().endswith(('.', '?', '!'))
        
        # Merge if:
        # - No terminal punctuation AND
        # - Gap is small enough AND
        # - Combined length is under threshold
        should_merge = (
            not has_terminal and
            gap <= max_gap and
            len(combined_text) <= max_chars
        )
        
        if should_merge:
            # Merge into current
            current['end'] = seg['end']
            current['text'] = combined_text
        else:
            # Save current and start new
            merged.append(current)
            current = {
                'start': seg['start'],
                'end': seg['end'],
                'text': text
            }
    
    # Don't forget the last one
    merged.append(current)
    
    return merged


def write_srt(segments: List[Dict[str, Any]], output_path: Path) -> None:
    """Write segments to SRT file.
    
    Args:
        segments: List of segments with start, end, text
        output_path: Output SRT file path
    """
    with output_path.open('w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{format_srt_timestamp(seg['start'])} --> {format_srt_timestamp(seg['end'])}\n")
            f.write(f"{seg['text']}\n\n")


def write_vtt(segments: List[Dict[str, Any]], output_path: Path) -> None:
    """Write segments to VTT file.
    
    Args:
        segments: List of segments with start, end, text
        output_path: Output VTT file path
    """
    with output_path.open('w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            f.write(f"{format_vtt_timestamp(seg['start'])} --> {format_vtt_timestamp(seg['end'])}\n")
            f.write(f"{seg['text']}\n\n")


def write_txt(segments: List[Dict[str, Any]], output_path: Path) -> None:
    """Write segments to plain text file.
    
    Args:
        segments: List of segments with start, end, text
        output_path: Output text file path
    """
    with output_path.open('w', encoding='utf-8') as f:
        for seg in segments:
            f.write(f"{seg['text']}\n")


def transliterate_to_devanagari(text: str) -> str:
    """Transliterate romanized Hindi/Sanskrit to Devanagari.
    
    Tries multiple transliteration schemes and picks the best result.
    
    Args:
        text: Input romanized text
        
    Returns:
        Transliterated text with Devanagari characters
    """
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
    except ImportError:
        print("ERROR: indic-transliteration library not installed", file=sys.stderr)
        print("Install with: pip install indic-transliteration", file=sys.stderr)
        return text
    
    # Try multiple schemes and pick the one with most Devanagari output
    schemes = [
        sanscript.ITRANS,
        sanscript.HK,
        sanscript.IAST
    ]
    
    best_result = text
    best_score = 0
    
    for scheme in schemes:
        try:
            result = transliterate(text, scheme, sanscript.DEVANAGARI)
            # Count Devanagari characters (U+0900 to U+097F)
            devanagari_count = sum(1 for c in result if '\u0900' <= c <= '\u097F')
            
            if devanagari_count > best_score:
                best_score = devanagari_count
                best_result = result
        except Exception:
            continue
    
    return best_result


def transliterate_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transliterate all segment texts to Devanagari.
    
    Args:
        segments: List of segments with text
        
    Returns:
        List of segments with transliterated text
    """
    return [
        {
            **seg,
            'text': transliterate_to_devanagari(seg['text'])
        }
        for seg in segments
    ]


def main() -> int:
    """Main entry point for post-processing."""
    parser = argparse.ArgumentParser(
        description="Post-process transcription outputs with merging and transliteration"
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing transcript files"
    )
    parser.add_argument(
        "--merge-captions",
        action="store_true",
        help="Merge adjacent captions into sentences"
    )
    parser.add_argument(
        "--devanagari",
        action="store_true",
        help="Transliterate to Devanagari script"
    )
    
    args = parser.parse_args()
    
    input_dir = args.input_dir
    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}", file=sys.stderr)
        return 1
    
    # Find transcript.srt file
    srt_path = input_dir / "transcript.srt"
    if not srt_path.exists():
        print(f"ERROR: transcript.srt not found in {input_dir}", file=sys.stderr)
        return 1
    
    # Parse original segments
    print(f"Parsing {srt_path}...")
    segments = parse_srt_file(srt_path)
    print(f"✓ Loaded {len(segments)} segments")
    
    # Process merging
    if args.merge_captions:
        print("Merging captions...")
        merged_segments = merge_captions(segments)
        print(f"✓ Merged into {len(merged_segments)} segments")
        
        # Write merged outputs
        write_srt(merged_segments, input_dir / "transcript.merged.srt")
        write_vtt(merged_segments, input_dir / "transcript.merged.vtt")
        write_txt(merged_segments, input_dir / "transcript.merged.txt")
        print("✓ Created transcript.merged.*")
    
    # Process Devanagari transliteration
    if args.devanagari:
        print("Transliterating to Devanagari...")
        dev_segments = transliterate_segments(segments)
        
        # Write Devanagari outputs
        write_srt(dev_segments, input_dir / "transcript.dev.srt")
        write_vtt(dev_segments, input_dir / "transcript.dev.vtt")
        write_txt(dev_segments, input_dir / "transcript.dev.txt")
        print("✓ Created transcript.dev.*")
    
    print("\n✓ Post-processing complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
