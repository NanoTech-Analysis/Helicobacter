from helpers import *
import plotly as plt

R45_PDB = 1.19971e-2
DELTA_C13_TANK = -34.73e-3
R45_TANK = (DELTA_C13_TANK + 1) *R45_PDB
DELTA_C13_HUMAN_PRE = -26.5e-3
R45_HUMAN_PRE = (DELTA_C13_HUMAN_PRE + 1) *R45_PDB

I44_BACKGROUND = 5e6
I45_BACKGROUND = 5.5e4

# REAL_TIME_MAIN_DIR = "C:/Users/39338/Desktop/file server - scambio - MANUAL SYNC/test_valvole"
# REAL_TIME_FILES_SOURCE_DIR = "C:/Users/39338/Desktop/file server - scambio - MANUAL SYNC/test_valvole/source_files"
REAL_TIME_MAIN_DIR = "C:/Users/Daniel Racca/NanoTech Analysis S.r.l/File Server - Scambio/Progetto_Helicobacter - ANALISI/bologna/caratterizzazione_proto_3"
REAL_TIME_FILES_SOURCE_DIR = "C:/Users/Daniel Racca/NanoTech Analysis S.r.l/File Server - Scambio/Progetto_Helicobacter - ANALISI/bologna/caratterizzazione_proto_3/spectra_match_target"


# PLOT_COLORS =  plt.colors.DEFAULT_PLOTLY_COLORS
PLOT_COLORS = [
    "rgb(214, 39, 40)",
    "rgb(255, 127, 14)",
    "rgb(10, 40, 200)",
    "rgb(40, 180, 255)",
]

PLOT_COLORS_REAL_TIME = [
    (255, 127, 14), # red
    (10, 40, 200), # blue
    (214, 39, 40), # orange
    (40, 180, 255), # light blue
    (0, 153, 76), # green
    (153, 153, 0), # light green
]

RESULTS_COLOR = {
    "before_pill": "rgb(0, 0, 0)",
    "after_pill": "rgb(0, 0, 0)",
}

ACTIVE_BUTTON_BACKGROUND_COLOR = "green"
ACTIVE_BUTTON_TEXT_COLOR = "white"
INACTIVE_BUTTON_BACKGROUND_COLOR = "white"
INACTIVE_BUTTON_TEXT_COLOR = "black"

MARKER_SIZE = 10

GUI_FONT_SIZE = 15
GUI_TABLE_FONT_SIZE = 12
GUI_LIST_HEIGHT = 40

R45_POSITIVITY_THRESHOLD = 5.0e-5

MASS_MARGIN_LEFT = 0.3
MASS_MARGIN_RIGHT = 0.3

# CO2 = Compound(
#     "CO2",
#     [
#         ExpectedPeak(
#             44,
#             is_main=True,
#             mass_margin_left=0.3,
#             mass_margin_right=0.3,
#         ),
#         ExpectedPeak(
#             45,
#             is_main=False,
#             mass_margin_left=0.3,
#             mass_margin_right=0.3,
#         ),
#         ExpectedPeak(
#             46,
#             is_main=False,
#             mass_margin_left=0.3,
#             mass_margin_right=0.3,
#         ),
#     ],
#     peaks_ratios_list = [
#         ([45], [44]),
#         ([46], [44]),
#         ([46], [44, 45]),
#     ]
# )

CO2_44_45 = Compound(
    "CO2_44_45",
    [
        ExpectedPeak(
            44,
            is_main=True,
            mass_margin_left=MASS_MARGIN_LEFT,
            mass_margin_right=MASS_MARGIN_RIGHT,
        ),
        ExpectedPeak(
            45,
            is_main=False,
            mass_margin_left=MASS_MARGIN_LEFT,
            mass_margin_right=MASS_MARGIN_RIGHT,
        ),
    ],
    peaks_ratios_list = [
        ([45], [44]),
    ]
)

CO2_HISTOGRAM = Compound(
    "CO2_HISTOGRAM",
    [
        ExpectedPeak(
            44,
            is_main=True,
            mass_margin_left=0,
            mass_margin_right=0,
        ),
        ExpectedPeak(
            45,
            is_main=False,
            mass_margin_left=0,
            mass_margin_right=0,
        ),
        ExpectedPeak(
            46,
            is_main=False,
            mass_margin_left=0,
            mass_margin_right=0,
        ),
    ],
    peaks_ratios_list = [
        ([45], [44]),
    ]
)


CO2_44_45_HISTOGRAM = Compound(
    "CO2_44_45",
    [
        ExpectedPeak(
            44,
            is_main=True,
            mass_margin_left=0,
            mass_margin_right=0,
        ),
        ExpectedPeak(
            45,
            is_main=False,
            mass_margin_left=0,
            mass_margin_right=0,
        ),
    ],
    peaks_ratios_list = [
        ([45], [44]),
    ]
)

CO2_Ar_HISTOGRAM = Compound(
    "CO2_Ar",
    [
        ExpectedPeak(
            40,
            is_main=False,
            mass_margin_left=0,
            mass_margin_right=0,
        ),
        ExpectedPeak(
            44,
            is_main=True,
            mass_margin_left=0,
            mass_margin_right=0,
        ),
        ExpectedPeak(
            45,
            is_main=False,
            mass_margin_left=0,
            mass_margin_right=0,
        ),
    ],
    peaks_ratios_list = [
        ([45], [44]),
    ]
)

CO2_44_45_shifted = Compound(
    "CO2_44_45_shifted",
    [
        ExpectedPeak(
            44.5,
            is_main=True,
            mass_margin_left=MASS_MARGIN_LEFT,
            mass_margin_right=MASS_MARGIN_RIGHT,
        ),
        ExpectedPeak(
            45.5,
            is_main=False,
            mass_margin_left=MASS_MARGIN_LEFT,
            mass_margin_right=MASS_MARGIN_RIGHT,
        ),
    ],
    peaks_ratios_list = [
        ([45.5], [44.5]),
    ]
)




