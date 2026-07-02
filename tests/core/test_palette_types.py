import pytest

from clim4cast_imagegen.core.palette_types import _build_palette_registry, RasterPalette


FAKE_RAW_PALETTES = {
    "AWP": {
        "colors": [(255, 0, 0)],
        "boundaries": [0.0, 1.0],
        "classes": [1],
        "continuous_coloring": False,
    },
    "AWD": {
        "colors": [(0, 255, 0)],
        "boundaries": [0.0, 2.0],
        "classes": [1, 2],
        "continuous_coloring": True,
    },
}

INVALID_RAW_PALETTES = [
    ({"AWP": {
        "boundaries": [0.0, 1.0],
        "classes": [1],
        "continuous_coloring": False,
    },}),
    ({"AWP": {
        "colors": [(0, 255, 0)],
        "classes": [1, 2],
        "continuous_coloring": True,
    },}),
    ({"AWP": {
        "colors": [(255, 0, 0)],
        "boundaries": [0.0, 1.0],
        "continuous_coloring": False,
    },}),
    ({"AWP": {
        "colors": [(0, 255, 0)],
        "boundaries": [0.0, 2.0],
        "classes": [1, 2],
    },}),
]


def test_build_palette_registry_fields():
    result = _build_palette_registry(FAKE_RAW_PALETTES, no_reclassify=set())
    palette = result["AWD"]

    assert isinstance(palette, RasterPalette)
    assert palette.colors == [(0, 255, 0)]
    assert palette.boundaries == [0.0, 2.0]
    assert palette.classes == [1, 2]
    assert palette.continuous_coloring is True


@pytest.mark.parametrize("raster_type, no_reclassify, expected",[
    ("AWP", {"AWP"}, False),
    ("AWD", {"AWP"}, True),
])
def test_build_palette_registry_reclassify_flag(
    raster_type,
    no_reclassify,
    expected
    ):
    result = _build_palette_registry(FAKE_RAW_PALETTES, no_reclassify)

    assert result[raster_type].reclassify == expected


def test_build_palette_registry_empty_input():
    result = _build_palette_registry({}, no_reclassify=set())

    assert result == {}


@pytest.mark.parametrize("palette", INVALID_RAW_PALETTES)
def test_build_palette_registry_missing_key_raises(palette):

    with pytest.raises(KeyError):
        _build_palette_registry(palette, no_reclassify=set())
