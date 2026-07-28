from datetime import date
from pathlib import Path

import pytest

from clim4cast_imagegen.io.local_storage import (
    create_data_folder_path,
    ensure_dir,
    find_png_files_grouped_by_dir,
    is_already_processed,
    iter_matching_files,
    mark_processed,
)

PARAMETERS = ["AWD_0-40cm", "FWI_GenZ", "DFM1H", "HI", "UTCI"]

CREATE_DATA_FOLDER_PATH_EXAMPLES = [
    (Path("test_folder"), date(2026, 6, 18), Path("test_folder/2026/2026-06-18")),
    (Path("test_folder"), date(2026, 1, 5), Path("test_folder/2026/2026-01-05"))
]


@pytest.mark.parametrize("main_path, today, expected", CREATE_DATA_FOLDER_PATH_EXAMPLES)
def test_create_data_folder_path(main_path, today, expected):
    result = create_data_folder_path(main_path, today)

    assert result == expected


def test_ensure_dir(tmp_path):
    target_folder = tmp_path / "new_folder" / "nested"

    ensure_dir(target_folder)

    assert target_folder.exists()
    assert target_folder.is_dir()


def test_grab_files(tmp_path):
    some_tif = tmp_path / "AWD_0-40cm_2026-06-18.tif"
    some_tif.touch()
    some_tif_upper = tmp_path / "FWI_GenZ_2026-06-18.TIF"
    some_tif_upper.touch()
    (tmp_path / "DFM1H_2026-06-18.tif").touch()
    (tmp_path / "HI_2026-06-18.tif").touch()
    (tmp_path / "UTCI_2026-06-18.tif").touch()
    invalid_tif = tmp_path / "some_file.tif"
    invalid_tif.touch()
    invalid_txt = tmp_path / "UTCI_2026-06-18.txt"
    invalid_txt.touch()

    result = list(iter_matching_files (tmp_path, parameters=PARAMETERS))

    assert len(result) == 5
    assert invalid_tif not in result
    assert invalid_txt not in result
    assert some_tif in result
    assert some_tif_upper in result


def test_grab_files_empty(tmp_path):
    result = list(iter_matching_files (tmp_path, parameters=PARAMETERS))

    assert result == []


def test_grab_files_finds_in_nested_subdirs(tmp_path):
    nested = tmp_path / "cs" / "2026"
    nested.mkdir(parents=True)
    nested_tif = nested / "UTCI_2026-06-18.tif"
    nested_tif.touch()

    result = list(iter_matching_files (tmp_path, parameters=PARAMETERS))

    assert nested_tif in result


def test_find_png_files_grouped_by_dir(tmp_path):
    (tmp_path / "root.png").touch()

    cs_dir = tmp_path / "cs"
    cs_dir.mkdir()
    (cs_dir / "bg_UTCI.png").touch()
    (cs_dir / "bg_HI.png").touch()

    nested_dir = tmp_path / "cs" / "reduced"
    nested_dir.mkdir()
    (nested_dir / "bg_AWD.png").touch()

    (tmp_path / "empty").mkdir()

    (cs_dir / "notes.txt").touch()

    result = find_png_files_grouped_by_dir(tmp_path)

    assert set(result.keys()) == {
        Path("."),
        Path("cs"),
        Path("cs") / "reduced",
    }
    assert result[Path(".")] == [tmp_path / "root.png"]
    assert sorted(result[Path("cs")]) == sorted([
        cs_dir / "bg_UTCI.png",
        cs_dir / "bg_HI.png",
    ])
    assert result[Path("cs") / "reduced"] == [nested_dir / "bg_AWD.png"]


def test_find_png_files_grouped_by_dir_empty_root(tmp_path):
    result = find_png_files_grouped_by_dir(tmp_path)

    assert result == {}


def test_marker_missing_file_is_not_processed(tmp_path):
    marker = tmp_path / "state" / "last_processed.txt"
    assert is_already_processed(date(2026, 7, 11), marker) is False


def test_marker_after_mark_is_processed(tmp_path):
    marker = tmp_path / "state" / "last_processed.txt"
    mark_processed(date(2026, 7, 11), marker)
    assert is_already_processed(date(2026, 7, 11), marker) is True


def test_marker_different_date_is_not_processed(tmp_path):
    marker = tmp_path / "state" / "last_processed.txt"
    mark_processed(date(2026, 7, 11), marker)
    assert is_already_processed(date(2026, 7, 12), marker) is False


def test_mark_processed_creates_state_dir(tmp_path):
    marker = tmp_path / "state" / "last_processed.txt"
    mark_processed(date(2026, 7, 11), marker)
    assert marker.exists()
    assert marker.read_text().strip() == "2026-07-11"
