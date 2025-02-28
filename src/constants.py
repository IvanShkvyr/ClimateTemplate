from pyproj import CRS

# PALETTES is a dictionary containing color palettes, boundary ranges, and class
# values for different climatic data types. Each key represents a specific
# climatic data type (e.g., "AWP", "AWD", "AWR", etc.), and each value contains:
# - "colors": A list of RGB color values used to represent different classes in
#       the data.
# - "boundaries": A list of boundary values that define the range for each class
# - "classes": A list of class values, where each class corresponds to a
#       specific range of values in the data.
# 
# The class values -999 and -1 are reserved for NoData values, representing
#   areas with no available data.
PALETTES = {
    "AWP": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (189, 0, 38),  # Extreme
            (240, 59, 32),  # Exceptional
            (253, 141, 60),  # Severe
            (254, 178, 76),  # Moderate
            (254, 217, 118),  # Minor
            (255, 255, 178),  # Slightly
            (255, 255, 255), # NoData (for other unclassified areas)
        ],
        "boundaries": [0, 1, 2, 3, 4, 5, 6],  # Corresponding to Slightly, Minor, Moderate, Severe, Exceptional, Extreme
        "classes": [-999, -1, 0, 1, 2, 3, 4, 5, 6],  # Class values corresponding to different ranges
    },
    "AWD": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (33, 102, 172),  # <-60
            (103, 169, 207),  # -31, -60
            (209, 229, 240),  # -1, -30
            (253, 219, 199),  # 0, 30
            (239, 138, 98),  # 31,60
            (178, 24, 43),  # > 60
        ],
        "boundaries": [-200, -60, -30, 0, 30, 60, 200],  # Corresponding ranges
        "classes": [-999, -1, 0, 1, 2, 3, 4, 5],  # Class values for AWD data
    },
    "AWR": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (241, 238, 246),  # <10
            (208, 209, 230),  # 11-30
            (166, 189, 219),  # 31-50
            (116, 169, 207),  # 51-70
            (43, 140, 190),  # 71-90
            (4, 90, 141),  # >90
        ],
        "boundaries": [0, 10, 30, 50, 70, 90, 100],  # Corresponding ranges
        "classes": [-999, -1, 0, 1, 2, 3, 4, 5],  # Class values for AWR data
    },
    "HI": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (254, 229, 217),  # 27–32°C – Caution
            (252, 174, 145),  # 32–41°C – Extreme Caution
            (251, 106, 74),  # 41–54°C – Danger
            (203, 24, 29),  # Above 54°C – Extreme Danger
        ],
        "boundaries": [-float("inf"), 32, 41, 54, 100],  # Temperature ranges in °C
        "classes": [-999, -1, 0, 1, 2, 3], # Class values for HI data
    },
    "UTCI": {
        "colors": [
            # (255, 255, 255),   # -999
            # (0, 255, 0),   # -1
            (5, 48, 97),  # less than -40°C
            (33, 102, 172),  # -40 – -27°C
            (67, 147, 195),  # -27 – -13°C
            (146, 197, 222),  # -13 – 0°C
            (209, 229, 240),  # 0 – 9°C
            (247, 247, 247),  # 9 – 26°C (no stress)
            (253, 219, 199),  # 26 – 32°C
            (244, 165, 130),  # 32 – 48°C
            (214, 96, 77),  # 38 – 46°C
            (178, 24, 43),  # more than 46°C
        ],
        "boundaries": [-100, -40, -27, -13, 0, 9, 26, 32, 38, 46, 100],  # Corresponding ranges
        "classes": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], # Class values for UTCI data
    },
    "FWI": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (145, 191, 219),  # Very Low
            (224, 243, 248),  # Low
            (255, 255, 191),  # Moderate
            (254, 224, 144),  # High
            (252, 141, 89),  # Very High
            (215, 48, 39),  # Extreme
        ],
        "boundaries": [1, 2, 3, 4, 5, 6],  # Categories from Very Low to Extreme
        "classes": [-999, -1, 1, 2, 3, 4, 5, 6], # Class values for FWI data
    },
    "DFM10H": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (178, 24, 43),  # Less than 6 %
            (214, 96, 77),  # 6–9 %
            (244, 165, 130),  # 9–12 %
            (253, 219, 199),  # 12–15 %
            (224, 224, 224),  # 15–25 %
            (186, 186, 186),  # 25–35 %
        ],
        "boundaries": [-0.9, 6, 9, 12, 15, 25, 35],  # Corresponding ranges
        "classes": [-999, -1, 0, 1, 2, 3, 4, 5],  # Class values for DFM10H data
    },
}

# List of parameter names representing different types of climate data
# These are used to search for corresponding images and templates.
PARAMETERS = [
    "AWD_0-40",  # Available Water Depth 0-40 cm
    "AWR_0-40",  # Available Water Reserve 0-40 cm
    "AWP_0-40",  # Available Water Potential 0-40 cm
    "AWD_0-100", # Available Water Depth 0-100 cm
    "AWR_0-100", # Available Water Reserve 0-100 cm
    "AWP_0-100", # Available Water Potential 0-100 cm
    "AWD_0-200", # Available Water Depth 0-200 cm
    "AWR_0-200", # Available Water Reserve 0-200 cm
    "AWP_0-200", # Available Water Potential 0-200 cm
    "FWI_GenZ",  # Fire Weather Index GenZ
    "DFM10H",    # Daily Fire Meteorological Index for 10 hours
    "HI",        # Heat Index
    "UTCI",      # Universal Thermal Climate Index
]

# CRS_FOR_DATA defines the coordinate reference system (CRS) that will be
# applied to the rasters and shapefiles used in the code.
# EPSG:3857 refers to the Web Mercator projection, which is commonly used for
# web-based mapping and is the chosen CRS for the project.
CRS_FOR_DATA = CRS.from_epsg(3857)

