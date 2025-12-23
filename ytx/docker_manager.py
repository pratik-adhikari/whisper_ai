"""Docker image and container management."""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional


DEFAULT_IMAGE_NAME = "whispercpp:cuda12"
DEFAULT_DOCKERFILE = "Dockerfile.whispercpp"


def check_docker_available() -> bool:
    """Check if Docker is available and running.
    
    Returns:
        True if Docker is available, False otherwise
    """
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def image_exists(image_name: str) -> bool:
    """Check if Docker image exists locally.
    
    Args:
        image_name: Name/tag of the Docker image
        
    Returns:
        True if image exists, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True,
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def build_image(
    dockerfile: Path,
    image_name: str,
    context_dir: Path,
    verbose: bool = False
) -> None:
    """Build Docker image.
    
    Args:
        dockerfile: Path to Dockerfile
        image_name: Name/tag for the built image
        context_dir: Build context directory
        verbose: If True, show build output
        
    Raises:
        subprocess.CalledProcessError: If build fails
    """
    cmd = [
        "docker", "build",
        "-f", str(dockerfile),
        "-t", image_name,
        str(context_dir)
    ]
    
    print(f"Building Docker image '{image_name}'...")
    print(f"This may take several minutes on first build...")
    
    if verbose:
        subprocess.run(cmd, check=True)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode, cmd)
    
    print(f"✓ Image '{image_name}' built successfully")


def run_container(
    image_name: str,
    url: str,
    output_dir: Path,
    model_path: Path,
    lang: str = "auto",
    threads: int = 8,
    verbose: bool = False
) -> None:
    """Run transcription in Docker container.
    
    Args:
        image_name: Docker image name/tag
        url: YouTube URL to transcribe
        output_dir: Host output directory (will be mounted to /out)
        model_path: Path to model file on host
        lang: Language code (or 'auto')
        threads: Number of threads for whisper-cli
        verbose: If True, show container output
        
    Raises:
        subprocess.CalledProcessError: If container fails
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "docker", "run",
        "--rm",
        "--gpus", "all",
        "-v", f"{output_dir.absolute()}:/out",
        "-v", f"{model_path.absolute()}:/model:ro",
        "-e", f"MODEL=/model",
        "-e", f"LANG={lang}",
        "-e", f"THREADS={threads}",
        image_name,
        url
    ]
    
    print(f"Running transcription in Docker container...")
    
    if verbose:
        subprocess.run(cmd, check=True)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode, cmd)
        # Show last few lines of output
        lines = result.stdout.strip().split("\n")
        for line in lines[-10:]:
            print(line)
