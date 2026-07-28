import numpy as np
import rasterio
from rasterio.transform import from_origin

from clim4cast_imagegen.io.raster_io import reclassify_raster


def _make_raster(path, data, nodata=-999.0):
    profile = {
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:3857",
        "transform": from_origin(0, 0, 10, 10),
    }
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)
    return path


def test_reclassify_maps_values_to_classes(tmp_path):
    data = np.array([[-5, 5, 15], [25, 35, 5]], dtype="float32")
    src = _make_raster(tmp_path / "input.tif", data)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = reclassify_raster(src, out_dir, [0, 10, 20, 30])

    with rasterio.open(result) as r:
        classes = r.read(1)

    expected = np.array([[-1, 0, 1], [2, 3, 0]], dtype="int16")
    assert np.array_equal(classes, expected)


def test_reclassify_writes_to_output_dir_with_same_name(tmp_path):
    src = _make_raster(tmp_path / "AWD_0-40cm.tif",
                       np.array([[1.0]], dtype="float32"))
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = reclassify_raster(src, out_dir, [0, 10])

    assert result.parent == out_dir
    assert result.name == "AWD_0-40cm.tif"
    assert result.exists()


def test_reclassify_output_is_int16(tmp_path):
    src = _make_raster(tmp_path / "input.tif",
                       np.array([[5.0, 15.0]], dtype="float32"))
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = reclassify_raster(src, out_dir, [0, 10, 20])

    with rasterio.open(result) as r:
        assert r.dtypes[0] == "int16"


def test_reclassify_defaults_nodata_when_source_has_none(tmp_path):
    src = _make_raster(tmp_path / "input.tif",
                       np.array([[5.0]], dtype="float32"), nodata=None)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = reclassify_raster(src, out_dir, [0, 10])

    with rasterio.open(result) as r:
        assert r.nodata == -999.0
