from pathlib import Path

from PIL import Image


def open_rgba(path: Path) -> Image.Image:
    """Open an image file and convert it to RGBA mode."""
    return Image.open(path).convert("RGBA")


def save_image(image: Image, dst_path: Path, **kwargs) -> None:
    """Save an image to file"""
    image.save(dst_path, **kwargs)


def trim_image_sides(
        image_path: Path,
        left: int = 0,
        right: int = 0,
        top: int = 0,
        bottom: int = 0,
    ) -> None:
    """
    Crop a fixed number of pixels from each side of an image, in place.
    """
    with Image.open(image_path) as img:
        img.load()
        width, height = img.size
        cropped = img.crop((left, top, width - right, height - bottom))

    cropped.save(image_path)
