import logging
from datetime import datetime
from pathlib import Path

import pytest

from clim4cast_imagegen.utils.pathname_utils import (
    extract_date,
    get_background_type,
    normalize_dfm_single_part,
    normalize_dfm_name_parts,
    build_new_filename,
)
from clim4cast_imagegen.core.exceptions import InvalidRasterDateError


EXTRACT_DATE_EXAMPLES = [
    (Path("AWD_0-100cm_2026-07-06.tif"), datetime(2026, 7, 6)),
    (Path("DFM1000H_2026-07-06.tif"), datetime(2026, 7, 6)),
    (Path("DFM1H_2026-07-01.tif"), datetime(2026, 7, 1)),
    (Path("FWI_GenZ_2026-07-10.tif"), datetime(2026, 7, 10)),
    (Path("HI_2026-07-10.tif"), datetime(2026, 7, 10)),
    (Path("UTCI_2026-07-10.tif"), datetime(2026, 7, 10)),
]

EXTRACT_DATE_EXAMPLES_NEGATIVE = [
    (Path("DFM1H_10000-07-01.tif")),
    (Path("AWD_0-100cm_2026-13-06.tif")),
    (Path("DFM1000H_2026-07-32.tif")),
]

GET_BACKGROUND_TYPE_EXAMPLES = [
    (Path("bg_AWD_0-200cm.png"), "AWD_0-200"),
    (Path("bg_AWR_0-40cm.png"), "AWR_0-40"),
    (Path("bg_DFM1H.png"), "DFM1H"),
    (Path("bg_FWI_GenZ.png"), "FWI_GenZ"),
    (Path("bg_HI.png"), "HI"),
    (Path("bg_UTCI.png"), "UTCI"),
]

NORMALIZE_DFM_SINGLE_PART_EXAMPLES = [
        ("DFM100", "DFM_100"),
        ("DFM1H", "DFM_1H"),
        ("AWP", "AWP"),
        ("DFM", "DFM"),
    ]

NORMALIZE_DFM_NAME_PARTS_EXAMPLES = [
        (['AWD', '0-100cm'], ['AWD', '0-100cm']),
        (['AWP', '0-40cm'], ['AWP', '0-40cm']),
        (['DFM1000H'], ['DFM_1000H']),
        (['DFM100H'], ['DFM_100H']),
        (['DFM10H'], ['DFM_10H']),
        (['DFM1H'], ['DFM_1H']),
        (['FWI', 'GenZ'], ['FWI', 'GenZ']),
        (['HI'], ['HI']),
        (['UTCI'], ['UTCI']),
    ]

BUILD_NEW_FILENAME_EXAMPLES = [
    (Path("AWD_0-100cm_2026-06-26.tif"), 3, "AWD_0-100cm_3.png"),
    (Path("AWP_0-40cm_2026-07-04.tif"), 8, "AWP_0-40cm_8.png"),
    (Path("DFM1000H_2026-06-26.tif"), 0, "DFM_1000H_0.png"),
    (Path("DFM10H_2026-07-03.tif"), 7, "DFM_10H_7.png"),
    (Path("HI_2026-06-27.tif"), 1, "HI_1.png"),
    (Path("UTCI_2026-07-04.tif"), 6, "UTCI_6.png"),
]


@pytest.mark.parametrize("path, expected", EXTRACT_DATE_EXAMPLES)
def test_extract_date_positive(path, expected):
    result = extract_date(path)

    assert result == expected


def test_extract_date_no_date_negative(caplog):
    with pytest.raises(InvalidRasterDateError):
        extract_date(Path("AWD_no_date_here.tif"))


@pytest.mark.parametrize("path", EXTRACT_DATE_EXAMPLES_NEGATIVE)
def test_extract_date_invalid_date_negative(caplog, path):
    with pytest.raises(InvalidRasterDateError):
        extract_date(path)


@pytest.mark.parametrize("path, expected", GET_BACKGROUND_TYPE_EXAMPLES)
def test_get_background_type(path, expected):
    result = get_background_type(path)

    assert result == expected


@pytest.mark.parametrize("raw, expected", NORMALIZE_DFM_SINGLE_PART_EXAMPLES)
def test_normalize_dfm_single_part(raw, expected):
    result = normalize_dfm_single_part(raw)

    assert result == expected


@pytest.mark.parametrize("parts, expected", NORMALIZE_DFM_NAME_PARTS_EXAMPLES)
def test_normalize_dfm_name_parts(parts, expected):
    result = normalize_dfm_name_parts(parts)

    assert result == expected


@pytest.mark.parametrize("path, index, expected", BUILD_NEW_FILENAME_EXAMPLES)
def test_build_new_filename(path, index, expected):
    result = build_new_filename(path, index)

    assert result == expected
