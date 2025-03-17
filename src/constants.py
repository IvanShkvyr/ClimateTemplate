from pyproj import CRS
import numpy as np

# PALETTES is a dictionary containing color palettes, boundary ranges, and class
# values for different climatic data types. Each key represents a specific
# climatic data type (e.g., "AWP", "AWD", "AWR", etc.), and each value contains:
# - "colors": A list of RGB color values used to represent different classes in
#       the data.
# - "boundaries": A list of boundary values that define the range for each class
# - "classes": A list of class values, where each class corresponds to a
#       specific range of values in the data.
# - "continuous_coloring": A boolean flag that determines whether to use a 
#       continuous color gradient between boundaries (True) or discrete classes
#       (False).
# 
# The class values -999 and -1 are reserved for NoData values, representing
#   areas with no available data.
PALETTES_V2 = {
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
        "continuous_coloring": False, # Enables continuous color gradient
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
        "continuous_coloring": False, # Enables continuous color gradient
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
        "continuous_coloring": False, # Enables continuous color gradient
    },
    "HI": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (255, 255, 255),  # < 27°C
            (254, 229, 217),  # 27–32°C – Caution
            (252, 174, 145),  # 32–41°C – Extreme Caution
            (251, 106, 74),  # 41–54°C – Danger
            (203, 24, 29),  # Above 54°C – Extreme Danger
        ],
        "boundaries": [-float("inf"), 27, 32, 41, 54, 100],  # Temperature ranges in °C
        "classes": [-999, -1, 0, 1, 2, 3, 4], # Class values for HI data
        "continuous_coloring": False, # Enables continuous color gradient
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
        "continuous_coloring": False, # Enables continuous color gradient
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
        "continuous_coloring": False, # Enables continuous color gradient
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
        "continuous_coloring": False, # Enables continuous color gradient
    },
}


PALETTES_V1 = {
    "AWP": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (140, 0, 0),  # Extreme
            (255, 0, 0),  # Exceptional
            (230, 76, 0),  # Severe
            (255, 170, 0),  # Moderate
            (255, 255, 0),  # Minor
            (255, 255, 190),  # Slightly
            (255, 255, 255), # NoData (for other unclassified areas)
        ],
        "boundaries": [0, 1, 2, 3, 4, 5, 6],  # Corresponding to Slightly, Minor, Moderate, Severe, Exceptional, Extreme
        "classes": [-999, -1, 0, 1, 2, 3, 4, 5, 6],  # Class values corresponding to different ranges
        "continuous_coloring": False, # Enables continuous color gradient
    },
    "AWD": {
        "colors": [
        (255, 255, 255),  # -999 (NoData)
        (np.int64(64), np.int64(11), np.int64(0)), # -100
        (np.int64(65), np.int64(10), np.int64(0)), # -99 
        (np.int64(66), np.int64(10), np.int64(0)), # -98 
        (np.int64(68), np.int64(10), np.int64(0)), # -97 
        (np.int64(69), np.int64(10), np.int64(0)), # -96 
        (np.int64(71), np.int64(9), np.int64(0)), # -95  
        (np.int64(72), np.int64(9), np.int64(0)), # -94  
        (np.int64(73), np.int64(9), np.int64(0)), # -93  
        (np.int64(75), np.int64(9), np.int64(0)), # -92  
        (np.int64(76), np.int64(8), np.int64(0)), # -91  
        (np.int64(78), np.int64(8), np.int64(0)), # -90  
        (np.int64(79), np.int64(8), np.int64(0)), # -89  
        (np.int64(80), np.int64(8), np.int64(0)), # -88  
        (np.int64(82), np.int64(7), np.int64(0)), # -87  
        (np.int64(83), np.int64(7), np.int64(0)), # -86  
        (np.int64(85), np.int64(7), np.int64(0)), # -85  
        (np.int64(86), np.int64(7), np.int64(0)), # -84  
        (np.int64(87), np.int64(6), np.int64(0)), # -83  
        (np.int64(89), np.int64(6), np.int64(0)), # -82  
        (np.int64(90), np.int64(6), np.int64(0)), # -81  
        (np.int64(92), np.int64(6), np.int64(0)), # -80  
        (np.int64(93), np.int64(8), np.int64(0)), # -79  
        (np.int64(95), np.int64(10), np.int64(0)), # -78 
        (np.int64(97), np.int64(13), np.int64(0)), # -77 
        (np.int64(99), np.int64(15), np.int64(0)), # -76 
        (np.int64(101), np.int64(18), np.int64(0)), # -75
        (np.int64(103), np.int64(20), np.int64(0)), # -74
        (np.int64(105), np.int64(22), np.int64(1)), # -73
        (np.int64(107), np.int64(25), np.int64(1)), # -72
        (np.int64(109), np.int64(27), np.int64(1)), # -71
        (np.int64(111), np.int64(30), np.int64(1)), # -70
        (np.int64(112), np.int64(32), np.int64(1)), # -69
        (np.int64(114), np.int64(34), np.int64(1)), # -68
        (np.int64(116), np.int64(37), np.int64(1)), # -67
        (np.int64(118), np.int64(39), np.int64(2)), # -66
        (np.int64(120), np.int64(42), np.int64(2)), # -65
        (np.int64(122), np.int64(44), np.int64(2)), # -64
        (np.int64(124), np.int64(46), np.int64(2)), # -63
        (np.int64(126), np.int64(49), np.int64(2)), # -62
        (np.int64(128), np.int64(51), np.int64(2)), # -61
        (np.int64(130), np.int64(54), np.int64(3)), # -60
        (np.int64(131), np.int64(57), np.int64(4)), # -59
        (np.int64(133), np.int64(61), np.int64(6)), # -58
        (np.int64(135), np.int64(64), np.int64(8)), # -57
        (np.int64(137), np.int64(68), np.int64(10)), # -56
        (np.int64(139), np.int64(72), np.int64(11)), # -55
        (np.int64(140), np.int64(75), np.int64(13)), # -54
        (np.int64(142), np.int64(79), np.int64(15)), # -53
        (np.int64(144), np.int64(83), np.int64(17)), # -52
        (np.int64(146), np.int64(86), np.int64(18)), # -51
        (np.int64(148), np.int64(90), np.int64(20)), # -50
        (np.int64(149), np.int64(94), np.int64(22)), # -49
        (np.int64(151), np.int64(97), np.int64(24)), # -48
        (np.int64(153), np.int64(101), np.int64(25)), # -47
        (np.int64(155), np.int64(105), np.int64(27)), # -46
        (np.int64(157), np.int64(108), np.int64(29)), # -45
        (np.int64(158), np.int64(112), np.int64(31)), # -44
        (np.int64(160), np.int64(116), np.int64(32)), # -43
        (np.int64(162), np.int64(119), np.int64(34)), # -42
        (np.int64(164), np.int64(123), np.int64(36)), # -41
        (np.int64(166), np.int64(127), np.int64(38)), # -40
        (np.int64(167), np.int64(129), np.int64(42)), # -39
        (np.int64(169), np.int64(132), np.int64(47)), # -38
        (np.int64(170), np.int64(134), np.int64(51)), # -37
        (np.int64(172), np.int64(137), np.int64(56)), # -36
        (np.int64(173), np.int64(139), np.int64(60)), # -35
        (np.int64(175), np.int64(142), np.int64(65)), # -34
        (np.int64(176), np.int64(144), np.int64(69)), # -33
        (np.int64(178), np.int64(147), np.int64(74)), # -32
        (np.int64(179), np.int64(149), np.int64(78)), # -31
        (np.int64(181), np.int64(152), np.int64(83)), # -30
        (np.int64(182), np.int64(155), np.int64(87)), # -29
        (np.int64(184), np.int64(157), np.int64(92)), # -28
        (np.int64(185), np.int64(160), np.int64(96)), # -27
        (np.int64(187), np.int64(162), np.int64(101)), # -26
        (np.int64(188), np.int64(165), np.int64(105)), # -25
        (np.int64(190), np.int64(167), np.int64(110)), # -24
        (np.int64(191), np.int64(170), np.int64(114)), # -23
        (np.int64(193), np.int64(172), np.int64(119)), # -22
        (np.int64(194), np.int64(175), np.int64(123)), # -21
        (np.int64(196), np.int64(178), np.int64(128)), # -20
        (np.int64(197), np.int64(180), np.int64(132)), # -19
        (np.int64(198), np.int64(182), np.int64(137)), # -18
        (np.int64(199), np.int64(184), np.int64(142)), # -17
        (np.int64(201), np.int64(186), np.int64(146)), # -16
        (np.int64(202), np.int64(189), np.int64(151)), # -15
        (np.int64(203), np.int64(191), np.int64(156)), # -14
        (np.int64(205), np.int64(193), np.int64(160)), # -13
        (np.int64(206), np.int64(195), np.int64(165)), # -12
        (np.int64(207), np.int64(197), np.int64(170)), # -11
        (np.int64(209), np.int64(200), np.int64(175)), # -10
        (np.int64(210), np.int64(202), np.int64(179)), # -9
        (np.int64(211), np.int64(204), np.int64(184)), # -8
        (np.int64(212), np.int64(206), np.int64(189)), # -7
        (np.int64(214), np.int64(208), np.int64(193)), # -6
        (np.int64(215), np.int64(211), np.int64(198)), # -5
        (np.int64(216), np.int64(213), np.int64(203)), # -4
        (np.int64(218), np.int64(215), np.int64(207)), # -3
        (np.int64(219), np.int64(217), np.int64(212)), # -2
        (np.int64(220), np.int64(219), np.int64(217)), # -1
        (np.int64(222), np.int64(222), np.int64(222)), # 0
        (np.int64(218), np.int64(220), np.int64(219)), # 1
        (np.int64(214), np.int64(219), np.int64(217)), # 2
        (np.int64(210), np.int64(218), np.int64(215)), # 3
        (np.int64(206), np.int64(216), np.int64(213)), # 4
        (np.int64(202), np.int64(215), np.int64(210)), # 5
        (np.int64(198), np.int64(214), np.int64(208)), # 6
        (np.int64(195), np.int64(212), np.int64(206)), # 7
        (np.int64(191), np.int64(211), np.int64(204)), # 8
        (np.int64(187), np.int64(210), np.int64(201)), # 9
        (np.int64(183), np.int64(209), np.int64(199)), # 10
        (np.int64(179), np.int64(207), np.int64(197)), # 11
        (np.int64(175), np.int64(206), np.int64(195)), # 12
        (np.int64(171), np.int64(205), np.int64(192)), # 13
        (np.int64(168), np.int64(203), np.int64(190)), # 14
        (np.int64(164), np.int64(202), np.int64(188)), # 15
        (np.int64(160), np.int64(201), np.int64(186)), # 16
        (np.int64(156), np.int64(199), np.int64(183)), # 17
        (np.int64(152), np.int64(198), np.int64(181)), # 18
        (np.int64(148), np.int64(197), np.int64(179)), # 19
        (np.int64(145), np.int64(196), np.int64(177)), # 20
        (np.int64(141), np.int64(194), np.int64(176)), # 21
        (np.int64(138), np.int64(193), np.int64(175)), # 22
        (np.int64(134), np.int64(191), np.int64(174)), # 23
        (np.int64(131), np.int64(190), np.int64(173)), # 24
        (np.int64(128), np.int64(188), np.int64(173)), # 25
        (np.int64(124), np.int64(187), np.int64(172)), # 26
        (np.int64(121), np.int64(185), np.int64(171)), # 27
        (np.int64(118), np.int64(184), np.int64(170)), # 28
        (np.int64(114), np.int64(182), np.int64(169)), # 29
        (np.int64(111), np.int64(181), np.int64(169)), # 30
        (np.int64(108), np.int64(179), np.int64(168)), # 31
        (np.int64(104), np.int64(178), np.int64(167)), # 32
        (np.int64(101), np.int64(176), np.int64(166)), # 33
        (np.int64(98), np.int64(175), np.int64(165)), # 34
        (np.int64(94), np.int64(173), np.int64(165)), # 35
        (np.int64(91), np.int64(172), np.int64(164)), # 36
        (np.int64(88), np.int64(170), np.int64(163)), # 37
        (np.int64(84), np.int64(169), np.int64(162)), # 38
        (np.int64(81), np.int64(167), np.int64(161)), # 39
        (np.int64(78), np.int64(166), np.int64(161)), # 40
        (np.int64(76), np.int64(163), np.int64(160)), # 41
        (np.int64(74), np.int64(160), np.int64(159)), # 42
        (np.int64(73), np.int64(157), np.int64(158)), # 43
        (np.int64(71), np.int64(154), np.int64(157)), # 44
        (np.int64(70), np.int64(151), np.int64(156)), # 45
        (np.int64(68), np.int64(148), np.int64(155)), # 46
        (np.int64(66), np.int64(145), np.int64(154)), # 47
        (np.int64(65), np.int64(142), np.int64(153)), # 48
        (np.int64(63), np.int64(139), np.int64(152)), # 49
        (np.int64(62), np.int64(136), np.int64(152)), # 50
        (np.int64(60), np.int64(133), np.int64(151)), # 51
        (np.int64(58), np.int64(130), np.int64(150)), # 52
        (np.int64(57), np.int64(127), np.int64(149)), # 53
        (np.int64(55), np.int64(124), np.int64(148)), # 54
        (np.int64(54), np.int64(121), np.int64(147)), # 55
        (np.int64(52), np.int64(118), np.int64(146)), # 56
        (np.int64(50), np.int64(115), np.int64(145)), # 57
        (np.int64(49), np.int64(112), np.int64(144)), # 58
        (np.int64(47), np.int64(109), np.int64(143)), # 59
        (np.int64(46), np.int64(107), np.int64(143)), # 60
        (np.int64(45), np.int64(104), np.int64(141)), # 61
        (np.int64(45), np.int64(102), np.int64(140)), # 62
        (np.int64(45), np.int64(100), np.int64(138)), # 63
        (np.int64(44), np.int64(97), np.int64(137)), # 64
        (np.int64(44), np.int64(95), np.int64(136)), # 65
        (np.int64(44), np.int64(93), np.int64(134)), # 66
        (np.int64(43), np.int64(90), np.int64(133)), # 67
        (np.int64(43), np.int64(88), np.int64(131)), # 68
        (np.int64(43), np.int64(86), np.int64(130)), # 69
        (np.int64(43), np.int64(84), np.int64(129)), # 70
        (np.int64(42), np.int64(81), np.int64(127)), # 71
        (np.int64(42), np.int64(79), np.int64(126)), # 72
        (np.int64(42), np.int64(77), np.int64(124)), # 73
        (np.int64(41), np.int64(74), np.int64(123)), # 74
        (np.int64(41), np.int64(72), np.int64(122)), # 75
        (np.int64(41), np.int64(70), np.int64(120)), # 76
        (np.int64(40), np.int64(67), np.int64(119)), # 77
        (np.int64(40), np.int64(65), np.int64(117)), # 78
        (np.int64(40), np.int64(63), np.int64(116)), # 79
        (np.int64(40), np.int64(61), np.int64(115)), # 80
        (np.int64(39), np.int64(59), np.int64(112)), # 81
        (np.int64(39), np.int64(58), np.int64(109)), # 82
        (np.int64(38), np.int64(56), np.int64(107)), # 83
        (np.int64(38), np.int64(55), np.int64(104)), # 84
        (np.int64(38), np.int64(54), np.int64(102)), # 85
        (np.int64(37), np.int64(52), np.int64(99)), # 86
        (np.int64(37), np.int64(51), np.int64(97)), # 87
        (np.int64(37), np.int64(49), np.int64(94)), # 88
        (np.int64(36), np.int64(48), np.int64(92)), # 89
        (np.int64(36), np.int64(47), np.int64(89)), # 90
        (np.int64(36), np.int64(45), np.int64(86)), # 91
        (np.int64(35), np.int64(44), np.int64(84)), # 92
        (np.int64(35), np.int64(42), np.int64(81)), # 93
        (np.int64(35), np.int64(41), np.int64(79)), # 94
        (np.int64(34), np.int64(40), np.int64(76)), # 95
        (np.int64(34), np.int64(38), np.int64(74)), # 96
        (np.int64(34), np.int64(37), np.int64(71)), # 97
        (np.int64(33), np.int64(35), np.int64(69)), # 98
        (np.int64(33), np.int64(34), np.int64(66)), # 99
        (np.int64(33), np.int64(33), np.int64(64)), # 100
        ],
        "boundaries": [-200, -99, -98, -97, -96, -95, -94, -93, -92, -91, -90, -89, -88, -87, -86, -85, -84, -83, -82, -81, -80, -79, -78, -77, -76, -75, -74, -73, -72, -71, -70, -69, -68, -67, -66, -65, -64, -63, -62, -61, -60, -59, -58, -57, -56, -55, -54, -53, -52, -51, -50, -49, -48, -47, -46, -45, -44, -43, -42, -41, -40, -39, -38, -37, -36, -35, -34, -33, -32, -31, -30, -29, -28, -27, -26, -25, -24, -23, -22, -21, -20, -19, -18, -17, -16, -15, -14, -13, -12, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 200],  # Corresponding ranges
        "classes": [-999, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199],  # Class values for AWD data
        "continuous_coloring": False, # Enables continuous color gradient
    },
    "AWR": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (np.int64(102), np.int64(60), np.int64(9)), # 0
            (np.int64(108), np.int64(65), np.int64(15)), # 1   
            (np.int64(114), np.int64(70), np.int64(21)), # 2   
            (np.int64(120), np.int64(75), np.int64(27)), # 3   
            (np.int64(126), np.int64(81), np.int64(34)), # 4   
            (np.int64(132), np.int64(86), np.int64(40)), # 5   
            (np.int64(138), np.int64(91), np.int64(46)), # 6   
            (np.int64(144), np.int64(97), np.int64(53)), # 7   
            (np.int64(150), np.int64(102), np.int64(59)), # 8  
            (np.int64(156), np.int64(107), np.int64(65)), # 9  
            (np.int64(163), np.int64(113), np.int64(72)), # 10 
            (np.int64(166), np.int64(117), np.int64(77)), # 11 
            (np.int64(170), np.int64(121), np.int64(83)), # 12 
            (np.int64(174), np.int64(125), np.int64(89)), # 13 
            (np.int64(178), np.int64(130), np.int64(95)), # 14 
            (np.int64(182), np.int64(134), np.int64(101)), # 15
            (np.int64(185), np.int64(138), np.int64(107)), # 16
            (np.int64(189), np.int64(143), np.int64(113)), # 17
            (np.int64(193), np.int64(147), np.int64(119)), # 18
            (np.int64(197), np.int64(151), np.int64(125)), # 19
            (np.int64(201), np.int64(156), np.int64(131)), # 20
            (np.int64(203), np.int64(160), np.int64(136)), # 21
            (np.int64(206), np.int64(164), np.int64(141)), # 22
            (np.int64(209), np.int64(169), np.int64(146)), # 23
            (np.int64(212), np.int64(173), np.int64(152)), # 24
            (np.int64(215), np.int64(178), np.int64(157)), # 25
            (np.int64(218), np.int64(182), np.int64(162)), # 26
            (np.int64(221), np.int64(186), np.int64(168)), # 27
            (np.int64(224), np.int64(191), np.int64(173)), # 28
            (np.int64(227), np.int64(195), np.int64(178)), # 29
            (np.int64(230), np.int64(200), np.int64(184)), # 30
            (np.int64(232), np.int64(203), np.int64(188)), # 31
            (np.int64(234), np.int64(206), np.int64(192)), # 32
            (np.int64(236), np.int64(210), np.int64(196)), # 33
            (np.int64(238), np.int64(213), np.int64(200)), # 34
            (np.int64(240), np.int64(217), np.int64(204)), # 35
            (np.int64(242), np.int64(220), np.int64(208)), # 36
            (np.int64(244), np.int64(223), np.int64(212)), # 37
            (np.int64(246), np.int64(227), np.int64(216)), # 38
            (np.int64(248), np.int64(230), np.int64(220)), # 39
            (np.int64(250), np.int64(234), np.int64(225)), # 40
            (np.int64(250), np.int64(235), np.int64(227)), # 41
            (np.int64(250), np.int64(237), np.int64(230)), # 42
            (np.int64(250), np.int64(239), np.int64(233)), # 43
            (np.int64(250), np.int64(241), np.int64(235)), # 44
            (np.int64(251), np.int64(243), np.int64(238)), # 45
            (np.int64(251), np.int64(244), np.int64(241)), # 46
            (np.int64(251), np.int64(246), np.int64(243)), # 47
            (np.int64(251), np.int64(248), np.int64(246)), # 48
            (np.int64(251), np.int64(250), np.int64(249)), # 49
            (np.int64(252), np.int64(252), np.int64(252)), # 50
            (np.int64(250), np.int64(250), np.int64(252)), # 51
            (np.int64(248), np.int64(249), np.int64(252)), # 52
            (np.int64(246), np.int64(248), np.int64(252)), # 53
            (np.int64(244), np.int64(247), np.int64(252)), # 54
            (np.int64(242), np.int64(246), np.int64(252)), # 55
            (np.int64(240), np.int64(244), np.int64(252)), # 56
            (np.int64(238), np.int64(243), np.int64(252)), # 57
            (np.int64(236), np.int64(242), np.int64(252)), # 58
            (np.int64(234), np.int64(241), np.int64(252)), # 59
            (np.int64(232), np.int64(240), np.int64(252)), # 60
            (np.int64(228), np.int64(237), np.int64(250)), # 61
            (np.int64(225), np.int64(234), np.int64(249)), # 62
            (np.int64(221), np.int64(232), np.int64(247)), # 63
            (np.int64(218), np.int64(229), np.int64(246)), # 64
            (np.int64(214), np.int64(227), np.int64(244)), # 65
            (np.int64(211), np.int64(224), np.int64(243)), # 66
            (np.int64(207), np.int64(221), np.int64(241)), # 67
            (np.int64(204), np.int64(219), np.int64(240)), # 68
            (np.int64(200), np.int64(216), np.int64(238)), # 69
            (np.int64(197), np.int64(214), np.int64(237)), # 70
            (np.int64(192), np.int64(210), np.int64(234)), # 71
            (np.int64(187), np.int64(206), np.int64(232)), # 72
            (np.int64(182), np.int64(202), np.int64(229)), # 73
            (np.int64(177), np.int64(198), np.int64(227)), # 74
            (np.int64(172), np.int64(194), np.int64(224)), # 75
            (np.int64(167), np.int64(190), np.int64(222)), # 76
            (np.int64(162), np.int64(186), np.int64(219)), # 77
            (np.int64(157), np.int64(182), np.int64(217)), # 78
            (np.int64(152), np.int64(178), np.int64(214)), # 79
            (np.int64(148), np.int64(175), np.int64(212)), # 80
            (np.int64(142), np.int64(170), np.int64(208)), # 81
            (np.int64(136), np.int64(166), np.int64(205)), # 82
            (np.int64(130), np.int64(162), np.int64(202)), # 83
            (np.int64(125), np.int64(158), np.int64(199)), # 84
            (np.int64(119), np.int64(154), np.int64(196)), # 85
            (np.int64(113), np.int64(149), np.int64(193)), # 86
            (np.int64(108), np.int64(145), np.int64(190)), # 87
            (np.int64(102), np.int64(141), np.int64(187)), # 88
            (np.int64(96), np.int64(137), np.int64(184)), # 89
            (np.int64(91), np.int64(133), np.int64(181)), # 90
            (np.int64(82), np.int64(128), np.int64(176)), # 91
            (np.int64(74), np.int64(123), np.int64(172)), # 92
            (np.int64(65), np.int64(118), np.int64(168)), # 93
            (np.int64(57), np.int64(114), np.int64(164)), # 94
            (np.int64(48), np.int64(109), np.int64(160)), # 95
            (np.int64(40), np.int64(104), np.int64(156)), # 96
            (np.int64(31), np.int64(100), np.int64(152)), # 97
            (np.int64(23), np.int64(95), np.int64(148)), # 98
            (np.int64(14), np.int64(90), np.int64(144)), # 99
            (np.int64(6), np.int64(86), np.int64(140)), # 100
        ],
        "boundaries": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100],  # Corresponding ranges
        "classes": [-999, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100],  # Class values for AWR data
        "continuous_coloring": False, # Enables continuous color gradient
    },
    "HI": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (np.int64(255), np.int64(255), np.int64(242)), # 0
            (np.int64(255), np.int64(255), np.int64(242)), # 24
            (np.int64(255), np.int64(255), np.int64(242)), # 25
            (np.int64(255), np.int64(255), np.int64(242)), # 26
            (np.int64(255), np.int64(255), np.int64(242)), # 27
            (np.int64(255), np.int64(255), np.int64(128)), # 28 +
            (np.int64(255), np.int64(255), np.int64(77)), # 29
            (np.int64(255), np.int64(255), np.int64(38)), # 30 +
            (np.int64(255), np.int64(247), np.int64(13)), # 31 +
            (np.int64(255), np.int64(235), np.int64(13)), # 32 +
            (np.int64(255), np.int64(223), np.int64(13)), # 33 +
            (np.int64(252), np.int64(204), np.int64(13)), # 34 +
            (np.int64(252), np.int64(188), np.int64(13)), # 35 +
            (np.int64(252), np.int64(173), np.int64(13)), # 36 +
            (np.int64(250), np.int64(159), np.int64(12)), # 37 +
            (np.int64(247), np.int64(143), np.int64(7)), # 38 +
            (np.int64(247), np.int64(131), np.int64(7)), # 39 +
            (np.int64(245), np.int64(119), np.int64(10)), # 40 +
            (np.int64(245), np.int64(108), np.int64(10)), # 41 +
            (np.int64(242), np.int64(100), np.int64(12)), # 42 +
            (np.int64(242), np.int64(93), np.int64(12)), # 43 +
            (np.int64(242), np.int64(89), np.int64(12)), # 44 +
            (np.int64(245), np.int64(80), np.int64(10)), # 45 +
            (np.int64(245), np.int64(76), np.int64(10)), # 46 +
            (np.int64(247), np.int64(67), np.int64(7)), # 47 +
            (np.int64(247), np.int64(63), np.int64(7)), # 48 +
            (np.int64(250), np.int64(54), np.int64(5)), # 49 +
            (np.int64(250), np.int64(50), np.int64(5)), # 50 +
            (np.int64(252), np.int64(40), np.int64(3)), # 51 +
            (np.int64(252), np.int64(32), np.int64(3)), # 52 +
            (np.int64(255), np.int64(17), np.int64(0)), # 53 +
            (np.int64(252), np.int64(0), np.int64(0)), # 54 +
            (np.int64(250), np.int64(0), np.int64(0)), # 55 +
            (np.int64(245), np.int64(0), np.int64(0)), # 56 +
            (np.int64(242), np.int64(0), np.int64(0)), # 57 +
            (np.int64(237), np.int64(0), np.int64(0)), # 58 +
            (np.int64(235), np.int64(0), np.int64(0)), # 59 +
            (np.int64(230), np.int64(0), np.int64(0)), # 60 +
            (np.int64(227), np.int64(0), np.int64(0)), # 61 +
            (np.int64(222), np.int64(0), np.int64(0)), # 62 +
            (np.int64(219), np.int64(0), np.int64(0)), # 63 +
            (np.int64(214), np.int64(0), np.int64(0)), # 64 +
            (np.int64(209), np.int64(0), np.int64(0)), # 65 +
            (np.int64(207), np.int64(0), np.int64(0)), # 66 +
            (np.int64(201), np.int64(0), np.int64(0)), # 67 +
            (np.int64(199), np.int64(0), np.int64(0)), # 68 +
            (np.int64(194), np.int64(0), np.int64(0)), # 69 +
            (np.int64(191), np.int64(0), np.int64(0)), # 70 +
            (np.int64(186), np.int64(0), np.int64(0)), # 71 +
            (np.int64(184), np.int64(0), np.int64(0)), # 72 +
            (np.int64(179), np.int64(0), np.int64(0)), # 73 +
            (np.int64(173), np.int64(0), np.int64(0)), # 74 +
            (np.int64(168), np.int64(0), np.int64(0)), # 76 +
            (np.int64(163), np.int64(0), np.int64(0)), # 78 +
            (np.int64(158), np.int64(0), np.int64(0)), # 81 +
            (np.int64(153), np.int64(0), np.int64(0)), # 84 +
            (np.int64(148), np.int64(0), np.int64(0)), # 87 +
            (np.int64(143), np.int64(0), np.int64(0)), # 90 +
            (np.int64(138), np.int64(0), np.int64(0)), # 93 +
            (np.int64(133), np.int64(0), np.int64(0)), # 96 +
            (np.int64(128), np.int64(0), np.int64(0)), # 100 +
        ],
        "boundaries": [-float("inf"), 0, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 76, 78, 81, 84, 87, 90, 93, 96, 100],  # Temperature ranges in °C
        "classes": [-999, -1, 0, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 76, 78, 81, 84, 87, 90, 93, 96, 100], # Class values for HI data
        "continuous_coloring": False, # Enables continuous color gradient
    },
    "UTCI": {
        "colors": [
            (np.int64(20), np.int64(20), np.int64(102)), # -100
            (np.int64(20), np.int64(20), np.int64(102)), # -99
            (np.int64(20), np.int64(21), np.int64(103)), # -98
            (np.int64(20), np.int64(21), np.int64(104)), # -97
            (np.int64(20), np.int64(22), np.int64(105)), # -96
            (np.int64(20), np.int64(22), np.int64(106)), # -95
            (np.int64(20), np.int64(23), np.int64(106)), # -94
            (np.int64(20), np.int64(23), np.int64(107)), # -93
            (np.int64(20), np.int64(24), np.int64(108)), # -92
            (np.int64(20), np.int64(24), np.int64(109)), # -91
            (np.int64(20), np.int64(25), np.int64(110)), # -90
            (np.int64(20), np.int64(25), np.int64(110)), # -89
            (np.int64(20), np.int64(26), np.int64(111)), # -88
            (np.int64(20), np.int64(26), np.int64(112)), # -87
            (np.int64(20), np.int64(27), np.int64(113)), # -86
            (np.int64(20), np.int64(27), np.int64(114)), # -85
            (np.int64(20), np.int64(28), np.int64(114)), # -84
            (np.int64(20), np.int64(28), np.int64(115)), # -83
            (np.int64(20), np.int64(29), np.int64(116)), # -82
            (np.int64(20), np.int64(29), np.int64(117)), # -81
            (np.int64(20), np.int64(30), np.int64(118)), # -80
            (np.int64(20), np.int64(30), np.int64(118)), # -79
            (np.int64(20), np.int64(31), np.int64(119)), # -78
            (np.int64(20), np.int64(31), np.int64(120)), # -77
            (np.int64(20), np.int64(32), np.int64(121)), # -76
            (np.int64(20), np.int64(32), np.int64(122)), # -75
            (np.int64(20), np.int64(33), np.int64(122)), # -74
            (np.int64(20), np.int64(33), np.int64(123)), # -73
            (np.int64(20), np.int64(34), np.int64(124)), # -72
            (np.int64(20), np.int64(34), np.int64(125)), # -71
            (np.int64(20), np.int64(35), np.int64(126)), # -70
            (np.int64(20), np.int64(36), np.int64(126)), # -69
            (np.int64(20), np.int64(36), np.int64(127)), # -68
            (np.int64(20), np.int64(37), np.int64(128)), # -67
            (np.int64(20), np.int64(37), np.int64(129)), # -66
            (np.int64(20), np.int64(38), np.int64(130)), # -65
            (np.int64(20), np.int64(38), np.int64(130)), # -64
            (np.int64(20), np.int64(39), np.int64(131)), # -63
            (np.int64(20), np.int64(39), np.int64(132)), # -62
            (np.int64(20), np.int64(40), np.int64(133)), # -61
            (np.int64(20), np.int64(40), np.int64(134)), # -60
            (np.int64(20), np.int64(41), np.int64(134)), # -59
            (np.int64(20), np.int64(41), np.int64(135)), # -58
            (np.int64(20), np.int64(42), np.int64(136)), # -57
            (np.int64(20), np.int64(42), np.int64(137)), # -56
            (np.int64(20), np.int64(43), np.int64(138)), # -55
            (np.int64(20), np.int64(43), np.int64(138)), # -54
            (np.int64(20), np.int64(44), np.int64(139)), # -53
            (np.int64(20), np.int64(44), np.int64(140)), # -52
            (np.int64(20), np.int64(45), np.int64(141)), # -51
            (np.int64(20), np.int64(45), np.int64(142)), # -50
            (np.int64(20), np.int64(46), np.int64(142)), # -49
            (np.int64(20), np.int64(46), np.int64(143)), # -48
            (np.int64(20), np.int64(47), np.int64(144)), # -47
            (np.int64(20), np.int64(47), np.int64(145)), # -46
            (np.int64(20), np.int64(48), np.int64(146)), # -45
            (np.int64(20), np.int64(48), np.int64(146)), # -44
            (np.int64(20), np.int64(49), np.int64(147)), # -43
            (np.int64(20), np.int64(49), np.int64(148)), # -42
            (np.int64(20), np.int64(50), np.int64(149)), # -41
            (np.int64(21), np.int64(51), np.int64(150)), # -40
            (np.int64(21), np.int64(55), np.int64(152)), # -39
            (np.int64(21), np.int64(59), np.int64(155)), # -38
            (np.int64(22), np.int64(63), np.int64(158)), # -37
            (np.int64(22), np.int64(67), np.int64(161)), # -36
            (np.int64(22), np.int64(71), np.int64(163)), # -35
            (np.int64(23), np.int64(75), np.int64(166)), # -34
            (np.int64(23), np.int64(79), np.int64(169)), # -33
            (np.int64(24), np.int64(83), np.int64(172)), # -32
            (np.int64(24), np.int64(87), np.int64(174)), # -31
            (np.int64(24), np.int64(91), np.int64(177)), # -30
            (np.int64(25), np.int64(95), np.int64(180)), # -29
            (np.int64(25), np.int64(99), np.int64(183)), # -28
            (np.int64(26), np.int64(103), np.int64(186)), # -27
            (np.int64(30), np.int64(108), np.int64(187)), # -26
            (np.int64(34), np.int64(113), np.int64(189)), # -25
            (np.int64(38), np.int64(119), np.int64(191)), # -24
            (np.int64(42), np.int64(124), np.int64(193)), # -23
            (np.int64(47), np.int64(129), np.int64(195)), # -22
            (np.int64(51), np.int64(135), np.int64(197)), # -21
            (np.int64(55), np.int64(140), np.int64(199)), # -20
            (np.int64(59), np.int64(145), np.int64(200)), # -19
            (np.int64(63), np.int64(151), np.int64(202)), # -18
            (np.int64(68), np.int64(156), np.int64(204)), # -17
            (np.int64(72), np.int64(161), np.int64(206)), # -16
            (np.int64(76), np.int64(167), np.int64(208)), # -15
            (np.int64(80), np.int64(172), np.int64(210)), # -14
            (np.int64(85), np.int64(178), np.int64(212)), # -13
            (np.int64(92), np.int64(183), np.int64(213)), # -12
            (np.int64(99), np.int64(189), np.int64(214)), # -11
            (np.int64(106), np.int64(194), np.int64(216)), # -10
            (np.int64(114), np.int64(200), np.int64(217)), # -9
            (np.int64(121), np.int64(205), np.int64(219)), # -8
            (np.int64(128), np.int64(211), np.int64(220)), # -7
            (np.int64(136), np.int64(216), np.int64(222)), # -6
            (np.int64(143), np.int64(222), np.int64(223)), # -5
            (np.int64(150), np.int64(227), np.int64(225)), # -4
            (np.int64(158), np.int64(233), np.int64(226)), # -3
            (np.int64(165), np.int64(238), np.int64(228)), # -2
            (np.int64(172), np.int64(244), np.int64(229)), # -1
            (np.int64(180), np.int64(250), np.int64(231)), # 0
            (np.int64(185), np.int64(250), np.int64(229)), # 1
            (np.int64(191), np.int64(250), np.int64(227)), # 2
            (np.int64(197), np.int64(250), np.int64(225)), # 3
            (np.int64(203), np.int64(250), np.int64(223)), # 4
            (np.int64(208), np.int64(250), np.int64(222)), # 5
            (np.int64(214), np.int64(250), np.int64(220)), # 6
            (np.int64(220), np.int64(250), np.int64(218)), # 7
            (np.int64(226), np.int64(250), np.int64(216)), # 8
            (np.int64(232), np.int64(250), np.int64(215)), # 9
            (np.int64(233), np.int64(248), np.int64(206)), # 10
            (np.int64(234), np.int64(247), np.int64(198)), # 11
            (np.int64(236), np.int64(246), np.int64(190)), # 12
            (np.int64(237), np.int64(244), np.int64(181)), # 13
            (np.int64(238), np.int64(243), np.int64(173)), # 14
            (np.int64(240), np.int64(242), np.int64(165)), # 15
            (np.int64(241), np.int64(240), np.int64(156)), # 16
            (np.int64(242), np.int64(239), np.int64(148)), # 17
            (np.int64(244), np.int64(238), np.int64(140)), # 18
            (np.int64(245), np.int64(237), np.int64(132)), # 19
            (np.int64(246), np.int64(235), np.int64(123)), # 20
            (np.int64(248), np.int64(234), np.int64(115)), # 21
            (np.int64(249), np.int64(233), np.int64(107)), # 22
            (np.int64(250), np.int64(231), np.int64(98)), # 23
            (np.int64(252), np.int64(230), np.int64(90)), # 24
            (np.int64(253), np.int64(229), np.int64(82)), # 25
            (np.int64(255), np.int64(228), np.int64(74)), # 26
            (np.int64(255), np.int64(213), np.int64(69)), # 27
            (np.int64(255), np.int64(199), np.int64(64)), # 28
            (np.int64(255), np.int64(185), np.int64(60)), # 29
            (np.int64(255), np.int64(171), np.int64(55)), # 30
            (np.int64(255), np.int64(157), np.int64(50)), # 31
            (np.int64(255), np.int64(143), np.int64(46)), # 32
            (np.int64(254), np.int64(129), np.int64(42)), # 33
            (np.int64(254), np.int64(116), np.int64(39)), # 34
            (np.int64(253), np.int64(103), np.int64(35)), # 35
            (np.int64(253), np.int64(89), np.int64(32)), # 36
            (np.int64(252), np.int64(76), np.int64(28)), # 37
            (np.int64(252), np.int64(63), np.int64(25)), # 38
            (np.int64(243), np.int64(60), np.int64(24)), # 39
            (np.int64(235), np.int64(57), np.int64(24)), # 40
            (np.int64(226), np.int64(54), np.int64(24)), # 41
            (np.int64(218), np.int64(51), np.int64(24)), # 42
            (np.int64(209), np.int64(48), np.int64(24)), # 43
            (np.int64(201), np.int64(45), np.int64(24)), # 44
            (np.int64(192), np.int64(42), np.int64(24)), # 45
            (np.int64(184), np.int64(40), np.int64(24)), # 46
            (np.int64(182), np.int64(39), np.int64(23)), # 47
            (np.int64(180), np.int64(38), np.int64(23)), # 48
            (np.int64(178), np.int64(37), np.int64(22)), # 49
            (np.int64(176), np.int64(37), np.int64(22)), # 50
            (np.int64(175), np.int64(36), np.int64(21)), # 51
            (np.int64(173), np.int64(35), np.int64(21)), # 52
            (np.int64(171), np.int64(34), np.int64(20)), # 53
            (np.int64(169), np.int64(34), np.int64(20)), # 54
            (np.int64(168), np.int64(33), np.int64(20)), # 55
            (np.int64(166), np.int64(32), np.int64(19)), # 56
            (np.int64(164), np.int64(31), np.int64(19)), # 57
            (np.int64(162), np.int64(31), np.int64(18)), # 58
            (np.int64(161), np.int64(30), np.int64(18)), # 59
            (np.int64(159), np.int64(29), np.int64(17)), # 60
            (np.int64(157), np.int64(28), np.int64(17)), # 61
            (np.int64(155), np.int64(28), np.int64(16)), # 62
            (np.int64(154), np.int64(27), np.int64(16)), # 63
            (np.int64(152), np.int64(26), np.int64(16)), # 64
            (np.int64(150), np.int64(25), np.int64(15)), # 65
            (np.int64(148), np.int64(25), np.int64(15)), # 66
            (np.int64(147), np.int64(24), np.int64(14)), # 67
            (np.int64(145), np.int64(23), np.int64(14)), # 68
            (np.int64(143), np.int64(22), np.int64(13)), # 69
            (np.int64(141), np.int64(22), np.int64(13)), # 70
            (np.int64(140), np.int64(21), np.int64(12)), # 71
            (np.int64(138), np.int64(20), np.int64(12)), # 72
            (np.int64(136), np.int64(20), np.int64(12)), # 73
            (np.int64(134), np.int64(19), np.int64(11)), # 74
            (np.int64(132), np.int64(18), np.int64(11)), # 75
            (np.int64(131), np.int64(17), np.int64(10)), # 76
            (np.int64(129), np.int64(17), np.int64(10)), # 77
            (np.int64(127), np.int64(16), np.int64(9)), # 78
            (np.int64(125), np.int64(15), np.int64(9)), # 79
            (np.int64(124), np.int64(14), np.int64(8)), # 80
            (np.int64(122), np.int64(14), np.int64(8)), # 81
            (np.int64(120), np.int64(13), np.int64(8)), # 82
            (np.int64(118), np.int64(12), np.int64(7)), # 83
            (np.int64(117), np.int64(11), np.int64(7)), # 84
            (np.int64(115), np.int64(11), np.int64(6)), # 85
            (np.int64(113), np.int64(10), np.int64(6)), # 86
            (np.int64(111), np.int64(9), np.int64(5)), # 87
            (np.int64(110), np.int64(8), np.int64(5)), # 88
            (np.int64(108), np.int64(8), np.int64(4)), # 89
            (np.int64(106), np.int64(7), np.int64(4)), # 90
            (np.int64(104), np.int64(6), np.int64(4)), # 91
            (np.int64(103), np.int64(5), np.int64(3)), # 92
            (np.int64(101), np.int64(5), np.int64(3)), # 93
            (np.int64(99), np.int64(4), np.int64(2)), # 94
            (np.int64(97), np.int64(3), np.int64(2)), # 95
            (np.int64(96), np.int64(2), np.int64(1)), # 96
            (np.int64(94), np.int64(2), np.int64(1)), # 97
            (np.int64(92), np.int64(1), np.int64(0)), # 98
            (np.int64(90), np.int64(0), np.int64(0)), # 99
            (np.int64(89), np.int64(0), np.int64(0)), # 100
        ],
        "boundaries": [-200, -99, -98, -97, -96, -95, -94, -93, -92, -91, -90, -89, -88, -87, -86, -85, -84, -83, -82, -81, -80, -79, -78, -77, -76, -75, -74, -73, -72, -71, -70, -69, -68, -67, -66, -65, -64, -63, -62, -61, -60, -59, -58, -57, -56, -55, -54, -53, -52, -51, -50, -49, -48, -47, -46, -45, -44, -43, -42, -41, -40, -39, -38, -37, -36, -35, -34, -33, -32, -31, -30, -29, -28, -27, -26, -25, -24, -23, -22, -21, -20, -19, -18, -17, -16, -15, -14, -13, -12, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 200],  # Corresponding ranges
        "classes": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199],  # Class values for AWD data
        "continuous_coloring": False, # Enables continuous color gradient
    },
    "FWI": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (75, 167, 64),  # Very Low
            (255, 244, 26),  # Low
            (252, 151, 50),  # Moderate
            (255, 41, 13),  # High
            (184, 0, 0),  # Very High
            (143, 43, 123),  # Extreme
        ],
        "boundaries": [1, 2, 3, 4, 5, 6],  # Categories from Very Low to Extreme
        "classes": [-999, -1, 1, 2, 3, 4, 5, 6], # Class values for FWI data
        "continuous_coloring": False, # Enables continuous color gradient
    },
    "DFM10H": {
        "colors": [
            (255, 255, 255),  # -999 (NoData)
            (255, 255, 255),  # -1 (NoData)
            (np.int64(115), np.int64(0), np.int64(0)), # 0
            (np.int64(127), np.int64(7), np.int64(0)), # 1     
            (np.int64(140), np.int64(15), np.int64(0)), # 2    
            (np.int64(153), np.int64(23), np.int64(0)), # 3    
            (np.int64(173), np.int64(32), np.int64(0)), # 4    
            (np.int64(193), np.int64(41), np.int64(0)), # 5    
            (np.int64(214), np.int64(50), np.int64(0)), # 6    
            (np.int64(224), np.int64(76), np.int64(10)), # 7   
            (np.int64(234), np.int64(102), np.int64(21)), # 8  
            (np.int64(245), np.int64(128), np.int64(32)), # 9  
            (np.int64(247), np.int64(158), np.int64(45)), # 10 
            (np.int64(249), np.int64(188), np.int64(58)), # 11 
            (np.int64(252), np.int64(219), np.int64(71)), # 12 
            (np.int64(253), np.int64(226), np.int64(94)), # 13 
            (np.int64(254), np.int64(234), np.int64(117)), # 14
            (np.int64(255), np.int64(242), np.int64(140)), # 15
            (np.int64(255), np.int64(246), np.int64(165)), # 16
            (np.int64(255), np.int64(250), np.int64(191)), # 17
            (np.int64(255), np.int64(255), np.int64(217)), # 18
            (np.int64(223), np.int64(231), np.int64(214)), # 19
            (np.int64(192), np.int64(207), np.int64(211)), # 20
            (np.int64(161), np.int64(183), np.int64(209)), # 21
            (np.int64(136), np.int64(164), np.int64(202)), # 22
            (np.int64(111), np.int64(146), np.int64(196)), # 23
            (np.int64(86), np.int64(127), np.int64(190)), # 24 
            (np.int64(62), np.int64(109), np.int64(184)), # 25 
            (np.int64(55), np.int64(98), np.int64(174)), # 26  
            (np.int64(49), np.int64(87), np.int64(164)), # 27  
            (np.int64(43), np.int64(76), np.int64(154)), # 28
            (np.int64(37), np.int64(65), np.int64(144)), # 29
            (np.int64(31), np.int64(55), np.int64(134)), # 30
            (np.int64(27), np.int64(46), np.int64(125)), # 31
            (np.int64(23), np.int64(37), np.int64(116)), # 32
            (np.int64(19), np.int64(28), np.int64(107)), # 33
            (np.int64(15), np.int64(19), np.int64(98)), # 34
            (np.int64(11), np.int64(11), np.int64(89)), # 35
        ],
        "boundaries": [-0.9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35],  # Corresponding ranges
        "classes": [-999, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35],  # Class values for DFM10H data
        "continuous_coloring": False, # Enables continuous color gradient
    }
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

