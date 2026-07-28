from PIL import Image

from clim4cast_imagegen.io.image_io import trim_image_sides


def test_trim_reduces_size(tmp_path):
    path = tmp_path / "img.png"
    Image.new("RGB", (100, 80), "blue").save(path)

    trim_image_sides(path, left=15, bottom=10)

    with Image.open(path) as img:
        assert img.size == (85, 70)


def test_trim_with_defaults_keeps_size(tmp_path):
    path = tmp_path / "img.png"
    Image.new("RGB", (50, 40), "blue").save(path)

    trim_image_sides(path)

    with Image.open(path) as img:
        assert img.size == (50, 40)


def test_trim_removes_the_correct_side(tmp_path):
    path = tmp_path / "img.png"
    img = Image.new("RGB", (10, 10), "blue")

    for y in range(10):
        img.putpixel((0, y), (255, 0, 0))
    img.save(path)

    trim_image_sides(path, left=1) 

    with Image.open(path) as result:
        colors = {result.getpixel((x, y)) for x in range(result.width)
                                          for y in range(result.height)}

    assert (255, 0, 0) not in colors
    assert result.size == (9, 10)
