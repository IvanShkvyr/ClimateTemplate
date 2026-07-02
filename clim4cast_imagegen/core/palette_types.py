from dataclasses import dataclass
from typing import List, Tuple, Dict

from clim4cast_imagegen.core.constants import PALETTES_V1, PALETTES_V2


@dataclass(frozen=True)
class RasterPalette:
    colors: List[Tuple]
    boundaries: List[float]
    classes: List[int]
    continuous_coloring: bool
    reclassify: bool


def _build_palette_registry(
        raw_palettes: Dict, no_reclassify: set[str]
    ) -> Dict[str, RasterPalette]:
    """
    Build a registry of RasterPalette objects from raw palette specs.
    """
    return {
        raster_type: RasterPalette(
            colors=spec["colors"],
            boundaries=spec["boundaries"],
            classes=spec["classes"],
            continuous_coloring=spec["continuous_coloring"],
            reclassify=raster_type not in no_reclassify,
        )
        for raster_type, spec in raw_palettes.items()
    }


PALETTE_REGISTRY_V1 = _build_palette_registry(
                                    PALETTES_V1, no_reclassify={"AWP", "FWI"}
                                    )

PALETTE_REGISTRY_V2 = _build_palette_registry(
                                    PALETTES_V2, no_reclassify={"AWP", "FWI"}
                                    )
