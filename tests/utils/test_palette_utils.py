from pathlib import Path

import pytest

from clim4cast_imagegen.utils.palette_utils import select_palette


SELECT_PALETTE_EXAMPLES = [
    (
        Path("normal/cs"),
        {
            "normal": {"AWD_0-100": [Path("AWD_0-100cm_2026-07-01.tif")]},
            "reduced": {"AWD_0-100": [Path("AWD_0-100cm_reduced.tif")]},
        },
        {"AWD_0-100": [Path("AWD_0-100cm_2026-07-01.tif")]},
    ),
    (
        Path("reduced/de"),
        {
            "normal": {"AWD_0-100": [Path("AWD_0-100cm_2026-07-01.tif")]},
            "reduced": {"AWD_0-100": [Path("AWD_0-100cm_reduced.tif")]},
        },
        {"AWD_0-100": [Path("AWD_0-100cm_reduced.tif")]},
    ),
]

SELECT_PALETTE_EXAMPLES_NEGATIVE = [
    (
        Path("invalid_folder/cs"),
        {
            "normal": {"AWD_0-100": [Path("AWD_0-100cm_2026-07-01.tif")]},
            "reduced": {"AWD_0-100": [Path("AWD_0-100cm_reduced.tif")]},
        },
    ),
    (
        Path("normal/cs"),
        {},
    ),
]


@pytest.mark.parametrize(
        "target_folder, visualizations, expected",
        SELECT_PALETTE_EXAMPLES
        )
def test_select_palette_positive(target_folder, visualizations, expected):
    result = select_palette(target_folder, visualizations)

    assert result == expected


@pytest.mark.parametrize(
        "target_folder, visualizations",
        SELECT_PALETTE_EXAMPLES_NEGATIVE
        )
def test_select_palette_invalid_key_negative(target_folder, visualizations):

    with pytest.raises(ValueError, match="Unknown palette folder"):
        select_palette(target_folder, visualizations)
