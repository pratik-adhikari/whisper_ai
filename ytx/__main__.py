"""Main CLI entry point for YouTube transcription tool."""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import __version__
from .metadata import extract_video_id, generate_output_folder_name
from .docker_manager import (
    check_docker_available,
    image_exists,
    build_image,
    run_container,
    DEFAULT_IMAGE_NAME,
    DEFAULT_DOCKERFILE
)


def update_meta_json(
    output_dir: Path,
    metadata: dict,
    run_date: str,
    url: str,
    model: str,
    lang: str,
    gpu_used: bool
) -> None:
    """Update meta.json with additional transcription metadata.
    
    Args:
        output_dir: Output directory path
        metadata: Video metadata from container
        run_date: Run date string (YYYY-MM-DD)
        url: Video URL
        model: Model name used
        lang: Language mode used
        gpu_used: Whether GPU was used
    """
    meta = {
        "run_date": run_date,
        "url": url,
        "video_id": metadata.get("id", ""),
        "title": metadata.get("title", ""),
        "channel": metadata.get("channel", metadata.get("uploader", "")),
        "upload_date": metadata.get("upload_date", ""),
        "duration": metadata.get("duration"),
        "webpage_url": metadata.get("webpage_url", url),
        "model": model,
        "lang_mode": lang,
        "gpu_used": gpu_used,
        "tool_version": __version__
    }
    
    meta_path = output_dir / "meta.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Updated {meta_path.name}")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Transcribe YouTube videos using whisper.cpp with CUDA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://www.youtube.com/watch?v=VIDEO_ID"
  %(prog)s "<url>" --model base --lang hi
  %(prog)s "<url>" --devanagari --merge-captions
  %(prog)s "<url>" --force --out-root /tmp/transcripts
        """
    )
    
    # Required arguments
    parser.add_argument(
        "url",
        help="YouTube video URL"
    )
    
    # Model and processing options
    parser.add_argument(
        "--model",
        default="large-v3",
        choices=["base", "medium", "large-v3"],
        help="Whisper model to use (default: large-v3)"
    )
    parser.add_argument(
        "--lang",
        default="auto",
        help="Language code (e.g., en, hi, de) or 'auto' for detection (default: auto)"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=8,
        help="Number of threads for transcription (default: 8)"
    )
    
    # Output options
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("./out"),
        help="Root directory for outputs (default: ./out)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output folder if it exists"
    )
    
    # Post-processing options
    parser.add_argument(
        "--devanagari",
        action="store_true",
        help="Enable Devanagari transliteration (creates .dev.* files)"
    )
    parser.add_argument(
        "--merge-captions",
        action="store_true",
        help="Merge caption segments into full sentences (creates .merged.* files)"
    )
    
    # Docker options
    parser.add_argument(
        "--image",
        default=DEFAULT_IMAGE_NAME,
        help=f"Docker image name (default: {DEFAULT_IMAGE_NAME})"
    )
    parser.add_argument(
        "--dockerfile",
        type=Path,
        default=None,
        help="Path to Dockerfile (default: auto-detect)"
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Force rebuild of Docker image"
    )
    
    # Other options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    args = parser.parse_args()
    
    # Check Docker availability
    if not check_docker_available():
        print("ERROR: Docker is not available or not running", file=sys.stderr)
        print("Please install Docker and ensure the daemon is running", file=sys.stderr)
        return 1
    
    # Determine Dockerfile path
    if args.dockerfile:
        dockerfile = args.dockerfile
    else:
        repo_root = Path(__file__).parent.parent
        dockerfile = repo_root / DEFAULT_DOCKERFILE
        if not dockerfile.exists():
            dockerfile = repo_root / "Dockerfile"
        if not dockerfile.exists():
            print(f"ERROR: Could not find Dockerfile", file=sys.stderr)
            return 1
    
    # Check/build Docker image
    if args.pull or not image_exists(args.image):
        try:
            build_image(
                dockerfile=dockerfile,
                image_name=args.image,
                context_dir=dockerfile.parent,
                verbose=args.verbose
            )
        except subprocess.CalledProcessError:
            print("ERROR: Failed to build Docker image", file=sys.stderr)
            return 1
    else:
        print(f"✓ Using existing image '{args.image}'")
    
    # Extract video ID from URL (no external dependencies)
    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"ERROR: Could not extract video ID from URL: {args.url}", file=sys.stderr)
        print("Please provide a valid YouTube URL", file=sys.stderr)
        return 1
    
    print(f"✓ Video ID: {video_id}")
    
    # Determine model path
    model_filename = f"ggml-{args.model}.bin"
    models_dir = Path(__file__).parent.parent / "models"
    model_path = models_dir / model_filename
    
    if not model_path.exists():
        print(f"ERROR: Model not found: {model_path}", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"Download model:", file=sys.stderr)
        print(f"  mkdir -p models", file=sys.stderr)
        print(f"  docker run --rm --entrypoint bash \\", file=sys.stderr)
        print(f"    -v $PWD/models:/models {args.image} \\", file=sys.stderr)
        model_name = args.model.split('-')[0] if args.model != 'large-v3' else 'large-v3'
        print(f"    -c 'cd /opt/whisper_models_scripts && ./download-ggml-model.sh {model_name} && mv -f {model_filename} /models/'", file=sys.stderr)
        return 1
    
    # Create temporary output folder
    run_date = datetime.now().strftime("%Y-%m-%d")
    temp_folder_name = f"{run_date}__temp__{video_id}"
    temp_output_dir = args.out_root / temp_folder_name
    temp_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run transcription in Docker (container does everything: metadata, download, transcribe)
    print(f"Starting transcription...")
    try:
        run_container(
            image_name=args.image,
            url=args.url,
            output_dir=temp_output_dir,
            model_path=model_path,
            lang=args.lang,
            threads=args.threads,
            verbose=args.verbose
        )
    except subprocess.CalledProcessError:
        print("ERROR: Transcription failed", file=sys.stderr)
        # Clean up temp folder
        import shutil
        shutil.rmtree(temp_output_dir, ignore_errors=True)
        return 1
    
    # Load metadata from container output
    metadata_file = temp_output_dir / "metadata.json"
    if not metadata_file.exists():
        print(f"ERROR: Container did not create metadata.json", file=sys.stderr)
        return 1
    
    with metadata_file.open('r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    print(f"\n✓ Title: {metadata.get('title', 'Unknown')}")
    print(f"✓ Channel: {metadata.get('channel', metadata.get('uploader', 'Unknown'))}")
    if metadata.get('duration'):
        print(f"✓ Duration: {metadata.get('duration')} seconds")
    
    # Generate final folder name
    final_folder_name = generate_output_folder_name(metadata, run_date)
    final_output_dir = args.out_root / final_folder_name
    
    # Check if final folder exists
    if final_output_dir.exists() and final_output_dir != temp_output_dir and not args.force:
        print(f"\nERROR: Output folder already exists: {final_output_dir}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        import shutil
        shutil.rmtree(temp_output_dir)
        return 1
    
    # Rename to final folder
    if final_output_dir.exists() and args.force:
        import shutil
        shutil.rmtree(final_output_dir)
    
    if temp_output_dir != final_output_dir:
        temp_output_dir.rename(final_output_dir)
        print(f"✓ Output folder: {final_output_dir}")
    
    # Update meta.json with run_date, model, tool_version, etc.
    update_meta_json(
        output_dir=final_output_dir,
        metadata=metadata,
        run_date=run_date,
        url=args.url,
        model=args.model,
        lang=args.lang,
        gpu_used=True
    )
    
    # Run post-processing if requested (requires indic-transliteration on host)
    if args.devanagari or args.merge_captions:
        print(f"\nRunning post-processing...")
        postprocess_script = Path(__file__).parent.parent / "scripts" / "postprocess.py"
        
        if not postprocess_script.exists():
            print(f"WARNING: postprocess.py not found, skipping", file=sys.stderr)
        else:
            cmd = [sys.executable, str(postprocess_script), str(final_output_dir)]
            if args.devanagari:
                cmd.append("--devanagari")
            if args.merge_captions:
                cmd.append("--merge-captions")
            
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                print("WARNING: Post-processing failed", file=sys.stderr)
    
    print(f"\n✅ Transcription complete!")
    print(f"   Output: {final_output_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
