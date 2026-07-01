from pathlib import Path

from PIL import Image


def open_rgba(path: Path) -> Image.Image:
    """Open an image file and convert it to RGBA mode."""
    return Image.open(path).convert("RGBA")


def save_image(image: Image, dst_path: Path, **kwargs) -> None:
    """Save an image to file"""
    image.save(dst_path, **kwargs)
