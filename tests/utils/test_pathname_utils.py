from pathlib import Path

import pytest

from clim4cast_imagegen.utils.pathname_utils import (
    normalize_dfm_single_part,
    build_new_filename,
)


PART_EXAMPLES = [
        ("DFM100", "DFM_100"),
        ("DFM1H", "DFM_1H"),
        ("AWP", "AWP"),
        ("DFM", "DFM"),
    ]

PATH_EXAMPLES = [
    (Path(r"AWD_0-100cm_2026-06-26.tif"), 3, "AWD_0-100cm_3.png"),
    (Path(r"AWP_0-40cm_2026-07-04.tif"), 8, "AWP_0-40cm_8.png"),
    (Path(r"DFM1000H_2026-06-26.tif"), 0, "DFM_1000H_0.png"),
    (Path(r"DFM10H_2026-07-03.tif"), 7, "DFM_10H_7.png"),
    (Path(r"HI_2026-06-27.tif"), 1, "HI_1.png"),
    (Path(r"UTCI_2026-07-04.tif"), 6, "UTCI_6.png"),
]


@pytest.mark.parametrize("raw, expected", PART_EXAMPLES)
def test_normalize_dfm_single_part(raw, expected):
    result = normalize_dfm_single_part(raw)

    assert result == expected


@pytest.mark.parametrize("path, index, expected", PATH_EXAMPLES)
def test_build_new_filename(path, index, expected):
    result = build_new_filename(path, index)

    assert result == expected
