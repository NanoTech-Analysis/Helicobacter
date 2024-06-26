# caricare dati solo quando il paziente viene selezionato
# plot split picchi
# ingrandire controlli vari
 # bottone per creare paziente
# controlla messaggi errore

import sys
from analysis import *
import os
from globals import *
import numpy as np
import re

from PySide6.QtWidgets import (
    QWidget,
    QApplication,
    QMainWindow,
    QComboBox,
    QTableWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidgetItem,
    QLabel,
    QCheckBox,
    QPushButton, QLineEdit, QAbstractScrollArea, QSpinBox,
)
from PySide6.QtCore import QTimer, Qt, QSize, QRectF
from PySide6.QtGui import QBrush, QColor, QFont

import pyqtgraph as pg


### COMMANDS
MAIN_DIR = REAL_TIME_MAIN_DIR
FILES_SOURCE_DIR = REAL_TIME_FILES_SOURCE_DIR

# EXPECTED_COMPOUND = CO2_44_45_HISTOGRAM
# PEAKS_MASS = [44, 45]
# ACTAUL_MASS_LIST = [44, 45]

EXPECTED_COMPOUND = CO2_HISTOGRAM
PEAKS_MASS = [44, 45, 46]
ACTAUL_MASS_LIST = [44, 45, 46]

#
# EXPECTED_COMPOUND = CO2_Ar_HISTOGRAM
# PEAKS_MASS = [44, 45]
# ACTAUL_MASS_LIST = [44, 45]


# EXPECTED_COMPOUND = CO2_44_45_shifted
# PEAKS_MASS = [44, 45]
# ACTAUL_MASS_LIST = [44.5, 45.5]

N_EXPECTED_PEAKS = len(EXPECTED_COMPOUND.expected_peaks)

# PEAK_MODE = "max"
# # PEAK_MODE = "area"
# PEAKS_VALUE_FUNCTION = lambda x: x.max() if PEAK_MODE=="max" else x.mean()
# PEAKS_VALUE_STR = "max value for peaks" if PEAK_MODE=="max" else "area value for peaks"

# def sub_area(
#     x,
#     n_point_left,
#     n_point_right,
# ):
#     max_index = x.argmax()
#     left_index = max_index-n_point_left
#     right_index = max_index+n_point_right + 1
#     sub_x = x[ left_index : right_index]
#     print("left points", n_point_left, "right points", n_point_right)
#     print(max_index)
#     print("left index", left_index, "right index",right_index)
#     print(x)
#     print(sub_x)
#     mean = sub_x.mean()
#     return mean

# trapezoid
# def sub_area(
#     x,
#     n_point_left,
#     n_point_right,
# ):
#     max_index = x.argmax()
#     left_index = max_index-n_point_left
#     right_index = max_index+n_point_right + 1
#     sub_x = x[ left_index : right_index]
#     area = 0
#     print(sub_x)
#     if len(sub_x) >1:
#         for i in range(len(sub_x)-1):
#             print(len(sub_x), i, sub_x[i])
#             area += (sub_x[i] + sub_x[i+1] ) / 2
#
#     else:
#         area = sub_x[0]
#     return area

# highest N-points
# def sub_area(
#     x,
#     n_point_left,
#     n_point_right,
# ):
#     n = n_point_left + n_point_right
#     value = np.sort(x)[-1-n].mean()
#     # value = np.sort(x)[-1-n_point_left]
#     return value

def sub_area(
    x,
    n_point_left,
    n_point_right,
):
    return x.max()

# n_points_left =1
# n_points_right = 1
# PEAKS_VALUE_FUNCTION = lambda x: sub_area(x, n_points_left, n_points_right)
# PEAKS_VALUE_STR = f"subset area ({n_points_left},{n_points_right})"

PEAKS_FUNCTIONS_DICT = {
    "Single peak": lambda x: x.max(),
    "Area -1+1": lambda x: sub_area(x, 1, 1),
    "Area -2+2": lambda x: sub_area(x, 2, 2),
    "Area -2+3": lambda x: sub_area(x, 2, 3),
}

### GLOBALS
# SAMPLES_DIR = f"{MAIN_DIR}/samples"
# BACKGROUND_DIR =  f"{MAIN_DIR}/background"
# REFERENCE_DIR =  f"{MAIN_DIR}/reference"

PLOT_LIMITS_BY_RATIO = {
    "45/44": [0.0103, 0.0128],
    "46/(44+45)": [0.0034, 0.0048],
}


### LOAD DATA

### GUI
class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowState(Qt.WindowMaximized)
        # self.showMaximized()
        self.DATA_DICT = {}
        self.dates_pattern = re.compile("\d\d\d\d_\d\d_\d\d")
        self.TARGET_DIR = f"{MAIN_DIR}/trash"
        self.max_trash_size = 300
        self.last_spectrum = None
        self.reference_spectrum = None
        self.reference_46 = None

        # table with results
        self.results_table = QTableWidget()
        self.results_table_columns = [
            "",
            "Run",
            "# spectra",
            "R45",
            # "R45_err",
            "R46",
            "REF",
            "D",
            "D_err",
            "D_corr",
            "D_corr_err",
            "Pre",
            "Post",
        ]
        self.results_table_columns_width = [3, 175, 30, 70, 70, 5, 50, 50, 50, 50, 30, 30]
        # self.results_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.results_table.cellChanged.connect(self.results_table_cell_changed)
        self.results_table.cellClicked.connect(self.results_table_cell_changed_by_user)

        # DOB computation
        self.dob_label = QLabel("<b>DOB</b><br>Missing pre-pill data<br>Missing post-pill data")
        font = self.dob_label.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.dob_label.setFont(font)
        self.dob_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.DOB = None
        self.pre_avg = None
        self.post_avg = None
        self.pre_avg_corr = None
        self.post_corr = None

        # plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')

        # dropdown to choose type of plot, R45, peak 44, peak 45
        self.plot_types = [
            "DeltaC",
            "DeltaC - evolving average",
            # "DeltaC - corrected",
            "R45",
            # "R45 - evolving average",
            "R46",
            # "R46 - evolving average",
            "Peak 44",
            "Peak 45",
            "Peak 46",
            "Peaks normalized",
            # "bkg - R45",
            # "bkg - peak 44",
            # "bkg - peak 45",
            "spectrum",
            # "spectrum - full",
            # "spectrum - split",
            "Source pressure",
            "peak_44 / pressure",
            # "R45 - distribution",

        ]
        self.plot_type_list = QComboBox()
        self.plot_type_list.currentTextChanged.connect(self.update_plot())
        self.plot_type_list.setFixedSize(QSize(300, GUI_LIST_HEIGHT))
        font = self.plot_type_list.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.plot_type_list.setFont(font)
        self.plot_type_list.addItems(self.plot_types)

        self.plot_type_label = QLabel("<b>Plot type:</b>")
        font = self.plot_type_label.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.plot_type_label.setFont(font)
        self.plot_type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # list of dates to choose from
        self.dates_list = QComboBox()
        self.dates_list.currentTextChanged.connect(self.load_data)
        self.dates_list.setFixedSize(QSize(150, GUI_LIST_HEIGHT))
        font = self.dates_list.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.dates_list.setFont(font)
        self.DATES = list(reversed(list(x for x in os.listdir(MAIN_DIR) if self.dates_pattern.match(x)) ))
        self.dates_list.addItems(self.DATES)


        self.dates_label = QLabel("<b>Date:</b>")
        font = self.dates_label.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.dates_label.setFont(font)
        self.dates_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # list of patient to choose from
        self.patient_list = QComboBox()
        self.patient_list.currentTextChanged.connect(self.show_new_patient)
        self.patient_list.setFixedSize(QSize(80, GUI_LIST_HEIGHT))
        font = self.patient_list.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.patient_list.setFont(font)

        self.patient_label = QLabel("<b>Patient:</b>")
        font = self.patient_label.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.patient_label.setFont(font)
        self.patient_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # checkbox to control background removal
        # self.background_checkbox = QCheckBox("Remove background")
        # font = self.background_checkbox.font()
        # font.setPointSize(GUI_FONT_SIZE)
        # self.background_checkbox.setFont(font)
        # self.background_checkbox.setCheckState(Qt.Checked)
        # self.background_checkbox.setCheckState(Qt.Unchecked)
        # self.background_checkbox.stateChanged.connect(self.update_data)

        # self.background_alert = QLabel()
        # self.background_alert.setText("")
        # font = self.background_alert.font()
        # font.setBold(True )
        # self.background_alert.setFont(font)
        # self.background_alert.setStyleSheet("QLabel { color : red; }")
        # self.background_alert.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        print()

        # # dropdown to select peak computation method
        # self.peak_methods_list = QComboBox()
        # self.peak_methods_list.setFixedSize(QSize(200, GUI_LIST_HEIGHT))
        # font = self.peak_methods_list.font()
        # font.setPointSize(GUI_FONT_SIZE)
        # self.peak_methods_list.setFont(font)
        # self.peak_methods_list.addItems([
        #     "Single peak",
        #     "Area -1+1",
        #     "Area -2+2",
        #     "Area -2+3",
        # ])
        # self.peak_methods_label = QLabel("<b>Peak method:</b>")
        # font = self.peak_methods_label.font()
        # font.setPointSize(GUI_FONT_SIZE)
        # self.peak_methods_label.setFont(font)
        # self.peak_methods_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)


        # counters to choose peak area width
        # self.peak_margin_left_input = QSpinBox()
        # self.peak_margin_left_input.setFixedSize(QSize(80, GUI_LIST_HEIGHT))
        # font = self.peak_margin_left_input.font()
        # font.setPointSize(GUI_FONT_SIZE)
        # self.peak_margin_left_input.setFont(font)
        # self.peak_margin_left_label = QLabel("Peak width left")
        # font = self.peak_margin_left_label.font()
        # font.setPointSize(GUI_FONT_SIZE)
        # self.peak_margin_left_label.setFont(font)
        # self.peak_margin_left_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        #
        # self.peak_margin_right_input = QSpinBox()
        # self.peak_margin_right_input.setFixedSize(QSize(80, GUI_LIST_HEIGHT))
        # font = self.peak_margin_right_input.font()
        # font.setPointSize(GUI_FONT_SIZE)
        # self.peak_margin_right_input.setFont(font)
        # self.peak_margin_right_label = QLabel("Peak width right")
        # font = self.peak_margin_right_label.font()
        # font.setPointSize(GUI_FONT_SIZE)
        # self.peak_margin_right_label.setFont(font)
        # self.peak_margin_right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # counters to choose the number of spectra to use to measure R46
        self.n_spectra_r46 = QSpinBox()
        self.n_spectra_r46.setFixedSize(QSize(80, GUI_LIST_HEIGHT))
        font = self.n_spectra_r46.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.n_spectra_r46.setFont(font)
        self.n_spectra_r46_label = QLabel("N spectra R46")
        font = self.n_spectra_r46_label.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.n_spectra_r46_label.setFont(font)
        self.n_spectra_r46_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # dropdown to select number of sample spectra
        self.samples_number_list = QComboBox()
        self.samples_number_list.setFixedSize(QSize(100, GUI_LIST_HEIGHT))
        font = self.samples_number_list.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.samples_number_list.setFont(font)
        self.samples_number_list.addItems(list(str(x) for x in  (10000, 500, 300, 200, 150,100, 75, 50, 25 ) ))
        self.samples_number_lable = QLabel("<b># samples:</b>")
        font = self.samples_number_lable.font()
        font.setPointSize(GUI_FONT_SIZE)
        self.samples_number_lable.setFont(font)
        self.samples_number_lable.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # controls to create patients and runs and to select the target directory
        controls_width = 200
        controls_height = 25
        self.add_run_edit_name = QLineEdit()
        self.add_run_edit_name.setPlaceholderText("New run name")
        self.add_run_edit_name.setFixedSize(QSize(controls_width, controls_height))
        self.add_run_button = QPushButton("Add run")
        self.add_run_button.clicked.connect(self.add_run)
        self.add_run_button.setFixedSize(QSize(controls_width, controls_height))

        self.target_run_label = QLabel("Target run for new spectra")
        self.target_run_list = QComboBox()
        self.target_run_list.currentTextChanged.connect(self.target_run_changed)
        self.target_run_list.setFixedSize(QSize(controls_width, controls_height))


        self.samples_button = QPushButton("Samples")
        self.background_button = QPushButton("Background")
        self.trash_button = QPushButton("Trash")
        self.samples_button.setFixedSize(QSize(controls_width, controls_height))
        self.background_button.setFixedSize(QSize(controls_width, controls_height))
        self.trash_button.setFixedSize(QSize(controls_width, controls_height))
        self.samples_button.clicked.connect(self.samples_button_clicked)
        self.background_button.clicked.connect(self.background_button_clicked)
        self.trash_button.clicked.connect(self.trash_button_clicked)
        self.trash_button.setStyleSheet("QPushButton {background-color: " +  ACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + ACTIVE_BUTTON_TEXT_COLOR + "}")
        self.samples_button.setStyleSheet("QPushButton {background-color: " + INACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + INACTIVE_BUTTON_TEXT_COLOR + "}")
        self.background_button.setStyleSheet("QPushButton {background-color: " +  INACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + INACTIVE_BUTTON_TEXT_COLOR + "}")

        self.reference_spectrum_button = QPushButton("Set reference")
        self.reference_spectrum_button.setFixedSize(QSize(controls_width, controls_height))
        self.reference_spectrum_button.clicked.connect(self.toggle_reference_spectrum)
        self.reference_spectrum_button.setStyleSheet("QPushButton {background-color: " + ACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + ACTIVE_BUTTON_TEXT_COLOR + "}")

        # create the main window layout
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.results_table)
        text_layout.addWidget(self.dob_label)
        text_layout.addWidget(self.add_run_button)
        text_layout.addWidget(self.add_run_edit_name)
        text_layout.addWidget(self.target_run_label)
        text_layout.addWidget(self.target_run_list)
        text_layout.addWidget(self.samples_button)
        text_layout.addWidget(self.background_button)

        trash_layout = QHBoxLayout()
        trash_layout.addWidget(self.trash_button)
        trash_layout.addWidget(self.reference_spectrum_button)

        text_layout.addLayout(trash_layout)

        text_layout.setSpacing(20)

        data_layout = QHBoxLayout()
        data_layout.addWidget(self.plot_widget)
        data_layout.addLayout(text_layout)

        patients_layout = QHBoxLayout()

        patients_layout.addWidget(self.dates_label)
        patients_layout.addWidget(self.dates_list)
        patients_layout.addWidget(self.patient_label)
        patients_layout.addWidget(self.patient_list)
        # patients_layout.addWidget(self.background_checkbox)
        # patients_layout.addWidget(self.background_alert)

        # patients_layout.addWidget(self.peak_methods_label)
        # patients_layout.addWidget(self.peak_methods_list)
        # patients_layout.addWidget(self.peak_margin_left_label)
        # patients_layout.addWidget(self.peak_margin_left_input)
        # patients_layout.addWidget(self.peak_margin_right_label)
        # patients_layout.addWidget(self.peak_margin_right_input)

        patients_layout.addWidget(self.n_spectra_r46_label)
        patients_layout.addWidget(self.n_spectra_r46)

        patients_layout.addWidget(self.plot_type_label)
        patients_layout.addWidget(self.plot_type_list)
        patients_layout.addWidget(self.samples_number_lable)
        patients_layout.addWidget(self.samples_number_list)
        patients_layout.setSpacing(10)

        main_layout = QVBoxLayout()
        main_layout.addLayout(patients_layout)
        main_layout.addLayout(data_layout)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.load_data()
        self.update_results_table()
        self.update_plot(force_show_all=True)

        # timer to check for new data for the selected patient
        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.run_update)
        self.timer.start()


    def load_sorted_patients(self):
        patients_numeric_raw =  list( int(x)  for x in os.listdir(self.SAMPLES_DIR) if x.isdigit() )
        patients_numeric_raw.sort()
        patients_numeric = list( str(x) for x in patients_numeric_raw)
        patients_not_numeric =  list( x  for x in os.listdir(self.SAMPLES_DIR) if not x.isdigit() )
        self.PATIENTS = patients_numeric + patients_not_numeric

    def add_run(self):
        current_patient = self.patient_list.currentText()
        new_run_name = self.add_run_edit_name.text().strip()
        if len(new_run_name) > 0:
            os.makedirs(f"{self.SAMPLES_DIR}/{current_patient}/{new_run_name}", exist_ok=True)
            os.makedirs(f"{self.BACKGROUND_DIR}/{current_patient}/{new_run_name}", exist_ok=True)
        self.add_run_edit_name.setText("")
        self.trash_button.click()

    def target_run_changed(self):
        self.target_run = self.target_run_list.currentText()
        self.trash_button.click()

    def samples_button_clicked(self):
        self.current_date = self.dates_list.currentText()
        current_patient = self.patient_list.currentText()
        target_run = self.target_run_list.currentText()
        self.TARGET_DIR = f"{MAIN_DIR}/{self.current_date}/samples/{current_patient}/{target_run}"
        self.samples_button.setStyleSheet("QPushButton {background-color: " +  ACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + ACTIVE_BUTTON_TEXT_COLOR+ "}")
        self.background_button.setStyleSheet("QPushButton {background-color: " + INACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + INACTIVE_BUTTON_TEXT_COLOR+ "}")
        self.trash_button.setStyleSheet("QPushButton {background-color: " +  INACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + INACTIVE_BUTTON_TEXT_COLOR+ "}")
        plot_type_index = self.plot_types.index("DeltaC")
        self.plot_type_list.setCurrentIndex(plot_type_index)
        self.reference_spectrum_button.setEnabled(False)
        self.reference_spectrum_button.setStyleSheet("QPushButton {background-color: " + "rgb(132,132,132)" + "; color: " + ACTIVE_BUTTON_TEXT_COLOR + "}")

    def background_button_clicked(self):
        pass
        # self.current_date = self.dates_list.currentText()
        # current_patient = self.patient_list.currentText()
        # target_run = self.target_run_list.currentText()
        # self.TARGET_DIR = f"{MAIN_DIR}/{self.current_date}/background/{current_patient}/{target_run}"
        # self.background_button.setStyleSheet("QPushButton {background-color: " +  ACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + ACTIVE_BUTTON_TEXT_COLOR+ "}")
        # self.samples_button.setStyleSheet("QPushButton {background-color: " + INACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + INACTIVE_BUTTON_TEXT_COLOR+ "}")
        # self.trash_button.setStyleSheet("QPushButton {background-color: " +  INACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + INACTIVE_BUTTON_TEXT_COLOR+ "}")
        # plot_type_index = self.plot_types.index("bkg - R45")
        # self.plot_type_list.setCurrentIndex(plot_type_index)
        # self.reference_spectrum_button.setEnabled(False)
        # self.reference_spectrum_button.setStyleSheet("QPushButton {background-color: " + "rgb(132,132,132)" + "; color: " + ACTIVE_BUTTON_TEXT_COLOR + "}")


    def trash_button_clicked(self):
        self.TARGET_DIR = f"{MAIN_DIR}/trash/"
        self.trash_button.setStyleSheet("QPushButton {background-color: " +  ACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + ACTIVE_BUTTON_TEXT_COLOR+ "}")
        self.samples_button.setStyleSheet("QPushButton {background-color: " + INACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + INACTIVE_BUTTON_TEXT_COLOR+ "}")
        self.background_button.setStyleSheet("QPushButton {background-color: " +  INACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + INACTIVE_BUTTON_TEXT_COLOR+ "}")
        # plot_type_index = self.plot_types.index("spectrum - full")
        plot_type_index = self.plot_types.index("spectrum")
        self.plot_type_list.setCurrentIndex(plot_type_index)
        self.reference_spectrum_button.setEnabled(True)
        reference_button_color = "rgb(254,110,0)" if self.reference_spectrum is not None else ACTIVE_BUTTON_BACKGROUND_COLOR
        self.reference_spectrum_button.setStyleSheet("QPushButton {background-color: " + reference_button_color + "; color: " + ACTIVE_BUTTON_TEXT_COLOR + "}")

    def toggle_reference_spectrum(self):
        if self.reference_spectrum == None:
            self.reference_spectrum = self.last_spectrum
            self.reference_spectrum_button.setText("Clear reference")
            self.reference_spectrum_button.setStyleSheet("QPushButton {background-color: " + "rgb(254,110,0)" +"; color: " + ACTIVE_BUTTON_TEXT_COLOR + "}")
        else:
            self.reference_spectrum = None
            self.reference_spectrum_button.setText("Set reference")
            self.reference_spectrum_button.setStyleSheet("QPushButton {background-color: " + ACTIVE_BUTTON_BACKGROUND_COLOR +"; color: " + ACTIVE_BUTTON_TEXT_COLOR + "}")


    def organize_files(self):
        new_files = os.listdir(FILES_SOURCE_DIR)
        if len(new_files) > 0   :
            os.makedirs(self.TARGET_DIR, exist_ok=True)
            last_file = new_files[-1]
            for f in new_files:
                if "trash" in self.TARGET_DIR.lower():
                    n_files = len(os.listdir(self.TARGET_DIR))
                    if n_files >= self.max_trash_size:
                        n_excess = n_files-self.max_trash_size + 1
                        files_to_delete = os.listdir(self.TARGET_DIR)[:n_excess]
                        for f_to_delete in files_to_delete:
                            os.remove(f"{self.TARGET_DIR}/{f_to_delete}")
                os.rename(f"{FILES_SOURCE_DIR}/{f}", f"{self.TARGET_DIR}/{f}")

            # peak_method = self.peak_methods_list.currentText()
            self.last_spectrum = Spectrum(
                file_path=f"{self.TARGET_DIR}/{last_file}",
                expected_compound=EXPECTED_COMPOUND,
                # peaks_value_function=PEAKS_VALUE_FUNCTION,
                # peaks_value_function = PEAKS_FUNCTIONS_DICT[peak_method]
                # peaks_value_function = lambda x: sub_area(x, self.peak_margin_left_input.value(), self.peak_margin_right_input.value())
                peaks_value_function=lambda x: sub_area(x, 0, 0),
            )

    def load_data(self):
        old_patient = self.patient_list.currentText()
        self.patient_list.clear()
        self.current_date = self.dates_list.currentText()

        self.SAMPLES_DIR = f"{MAIN_DIR}/{self.current_date}/samples"
        self.BACKGROUND_DIR = f"{MAIN_DIR}/{self.current_date}/background"
        self.REFERENCE_DIR = f"{MAIN_DIR}/{self.current_date}/reference"
        self.load_sorted_patients()
        self.patient_list.addItems(self.PATIENTS)
        try:
            old_patient_index = self.PATIENTS.index(old_patient)
        except:
            old_patient_index = 0
        self.patient_list.setCurrentIndex(old_patient_index)

        for patient in self.PATIENTS:
            self.DATA_DICT[patient] = {}

            # runs = list(reversed(os.listdir(f"{self.SAMPLES_DIR}/{patient}")))
            runs = list(os.listdir(f"{self.SAMPLES_DIR}/{patient}"))
            for run in runs:
                print()
                # print(f"Loading data for patient {patient} - run {run}")
                run_index = runs.index(run)
                files = os.listdir(f"{self.SAMPLES_DIR}/{patient}/{run}") [:int(self.samples_number_list.currentText()) ]
                files.sort()

                n_colors = len(PLOT_COLORS_REAL_TIME)
                run_color = PLOT_COLORS_REAL_TIME[run_index % n_colors]

                self.DATA_DICT[patient][run] = {
                    "files": files,
                    "peak_44": [],
                    "peak_45": [],
                    "peak_46": [],
                    "R45": [],
                    "R45_avg": 0,
                    "R45_avg_err": 0,
                    "R46": [],
                    "R46_avg": 0,
                    "R46_avg_err": 0,
                    "plot_44": None,
                    "plot_45": None,
                    "plot_46": None,
                    "plot_R45": None,
                    "plot_R46": None,
                    "color": run_color,
                    "background_peak_44": [],
                    "background_peak_45": [],
                    "background_R45": [],
                    "source_pressure": [],
                }

                for f in list(f for f in files if f!="2024_05_15_14_51_38.txt"):
                    print()
                    print(f)
                    # print(f, end='/r')
                    # peak_method = self.peak_methods_list.currentText()
                    try:
                        spectrum = Spectrum(
                            file_path=f"{self.SAMPLES_DIR}/{patient}/{run}/{f}",
                            expected_compound=EXPECTED_COMPOUND,
                            # peaks_value_function=PEAKS_VALUE_FUNCTION,
                            # peaks_value_function=PEAKS_FUNCTIONS_DICT[peak_method]
                            # peaks_value_function=lambda x: sub_area(x, self.peak_margin_left_input.value(), self.peak_margin_right_input.value())
                            peaks_value_function=lambda x: sub_area(x, 0, 0),
                        )
                    except Exception as e:
                        print(f"Error 1: {e.__class__.__name__} - {e}")
                        continue


                    for mass in PEAKS_MASS:
                        mass_index = PEAKS_MASS.index(mass)
                        actual_mass = ACTAUL_MASS_LIST[mass_index]

                        max_index = np.where(spectrum.available_peaks_mass == actual_mass)[0][0]
                        serial = spectrum.available_peaks_values[max_index]
                        self.DATA_DICT[patient][run][f"peak_{mass}"].append(serial)

                    # pressure
                    self.DATA_DICT[patient][run][f"source_pressure"].append(spectrum.source_pressure)


                self.DATA_DICT[patient][run]["R45"] = np.array(self.DATA_DICT[patient][run]["peak_45"]) / np.array(self.DATA_DICT[patient][run]["peak_44"])
                self.DATA_DICT[patient][run]["R45_avg"] = self.DATA_DICT[patient][run]["R45"].mean()
                self.DATA_DICT[patient][run]["R45_avg_err"] = np.sqrt( self.DATA_DICT[patient][run]["R45"].var() / len(self.DATA_DICT[patient][run]["files"]) )

                self.DATA_DICT[patient][run]["r46"] = np.array(self.DATA_DICT[patient][run]["peak_46"]) / np.array(self.DATA_DICT[patient][run]["peak_44"])
                self.DATA_DICT[patient][run]["r46_avg"] = self.DATA_DICT[patient][run]["r46"].mean()
                self.DATA_DICT[patient][run]["r46_avg_err"] = np.sqrt( self.DATA_DICT[patient][run]["r46"].var() / len(self.DATA_DICT[patient][run]["files"]) )

    def setup_results_table(self):
        self.results_table_tot_width = sum(self.results_table_columns_width)+100
        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(len(self.results_table_columns))
        self.results_table.setHorizontalHeaderLabels(self.results_table_columns)
        self.results_table.verticalHeader().setVisible(False)
        for i in range(len(self.results_table_columns)):
            self.results_table.setColumnWidth(i, self.results_table_columns_width[i])

        self.results_table.setFixedSize( QSize( self.results_table_tot_width, 200) )

    def run_update(self):
        self.organize_files()
        update_flag = self.update_data()

        if update_flag:
            self.update_results_table(keep_state=True)
            force_show_all = True if (self.pre_avg==None and self.post_avg==None) else False
            self.update_plot(force_show_all=force_show_all)

    def show_new_patient(self):
        self.update_results_table(keep_state=False)
        self.update_plot(force_show_all=True)

    def update_data(self):
        current_patient = self.patient_list.currentText()
        patient_dict = self.DATA_DICT[current_patient]

        # update the list of runs available as target for the new spectra
        available_target_runs = list( self.target_run_list.itemText(i) for i in range(self.target_run_list.count()) )
        for i in range(self.target_run_list.count()):
            if self.target_run_list.itemText(i) not in list( patient_dict.keys() ):
                self.target_run_list.removeItem(i)
        for run in list( patient_dict.keys() ):
            if run not in available_target_runs:
                self.target_run_list.addItem( run )

        old_patients = self.PATIENTS
        self.load_sorted_patients()
        if self.PATIENTS != old_patients:
        # if os.listdir(self.SAMPLES_DIR) != self.PATIENTS:
            self.load_data()
            update_flag = True
        else:
            update_flag = False

            if os.listdir(f"{self.SAMPLES_DIR}/{current_patient}")[:int(self.samples_number_list.currentText())] != list(patient_dict.keys()):
                self.load_data()
                update_flag = True

            else:
                for run in patient_dict.keys():
                    # if patient_dict[run].get("files") == None:

                    patient_dict[run]["files"] = os.listdir(f"{self.SAMPLES_DIR}/{current_patient}/{run}")[:int(self.samples_number_list.currentText())]

                    if True:
                        update_flag = True
                        # print(f"Updating data for {current_patient} - {run}")
                        for mass in PEAKS_MASS:
                            patient_dict[run][f"peak_{mass}"] = []
                            patient_dict[run][f"background_peak_{mass}"] = []

                        patient_dict[run][f"source_pressure"] = []

                        for f in patient_dict[run]["files"]:
                            # peak_method = self.peak_methods_list.currentText()
                            spectrum = Spectrum(
                                file_path=f"{self.SAMPLES_DIR}/{current_patient}/{run}/{f}",
                                expected_compound=EXPECTED_COMPOUND,
                                # peaks_value_function=PEAKS_VALUE_FUNCTION,
                                # peaks_value_function = PEAKS_FUNCTIONS_DICT[peak_method]
                                # peaks_value_function=lambda x: sub_area(x, self.peak_margin_left_input.value(), self.peak_margin_right_input.value())
                                peaks_value_function=lambda x: sub_area(x, 0, 0),
                            )

                            for mass in PEAKS_MASS:
                                mass_index = PEAKS_MASS.index(mass)
                                actual_mass = ACTAUL_MASS_LIST[mass_index]

                                max_index = np.where(spectrum.available_peaks_mass == actual_mass)[0][0]
                                serial = spectrum.available_peaks_values[max_index]
                                patient_dict[run][f"peak_{mass}"].append(serial)

                            # pressure
                            patient_dict[run][f"source_pressure"].append(spectrum.source_pressure)

                        # load background
                        # try:
                        #     background_files = os.listdir(f"{self.BACKGROUND_DIR}/{current_patient}/{run}")
                        #     n_bg_files = len(background_files)
                        #
                        #     for bg_f in background_files:
                        #         peak_method = "Single peak"
                        #         bg_spectrum = Spectrum(
                        #             file_path=f"{self.BACKGROUND_DIR}/{current_patient}/{run}/{bg_f}",
                        #             expected_compound=EXPECTED_COMPOUND,
                        #             # peaks_value_function=PEAKS_VALUE_FUNCTION,
                        #             # peaks_value_function=PEAKS_FUNCTIONS_DICT[peak_method]
                        #             peaks_value_function=lambda x: sub_area(x, self.peak_margin_left_input.value(), self.peak_margin_right_input.value())
                        #         )
                        #
                        #         for mass in PEAKS_MASS:
                        #             mass_index = PEAKS_MASS.index(mass)
                        #             actual_mass = ACTAUL_MASS_LIST[mass_index]
                        #
                        #             max_index = np.where(bg_spectrum.available_peaks_mass == actual_mass)[0][0]
                        #             serial = bg_spectrum.available_peaks_values[max_index]
                        #
                        #             patient_dict[run][f"background_peak_{mass}"].append(serial)
                        #
                        #
                        #     # self.background_alert.setText("")
                        #     patient_dict[run]["background_R45"] = np.array(patient_dict[run]["background_peak_45"]) / np.array(patient_dict[run]["background_peak_44"])
                        #
                        # except:
                        #     self.background_alert.setText(" (background not found)")
                        #     patient_dict[run]["background_R45"] = []
                        #     patient_dict[run]["background_peak_44"] = []
                        #     patient_dict[run]["background_peak_45"] = []


                        # if (
                        #         self.background_checkbox.checkState() == Qt.CheckState.Checked
                        #     and len(patient_dict[run]["background_peak_44"]) > 0
                        #     and len(patient_dict[run]["background_peak_45"]) > 0
                        # ):
                        # if False:
                        #     background_values_to_remove = {
                        #         "44": np.array(patient_dict[run]["background_peak_44"]).mean(),
                        #         "45": np.array(patient_dict[run]["background_peak_45"]).mean(),
                        #         "46": np.array(patient_dict[run]["background_peak_46"]).mean(),
                        #     }
                        #
                        # else:
                        #     background_values_to_remove = {
                        #         "44": 0,
                        #         "45": 0,
                        #         "46":0,
                        #     }

                        background_values_to_remove = {
                            "44": 0,
                            "45": 0,
                            "46":0,
                        }

                        for mass in PEAKS_MASS:
                            patient_dict[run][f"peak_{mass}"] = np.array(patient_dict[run][f"peak_{mass}"]) - background_values_to_remove[f"{mass}"]

                        try:
                            patient_dict[run]["R45"] = np.array(patient_dict[run]["peak_45"]) / np.array(patient_dict[run]["peak_44"])
                            patient_dict[run]["R45_avg"] = patient_dict[run]["R45"].mean()
                            patient_dict[run]["R45_avg_err"] = np.sqrt( patient_dict[run]["R45"].var() / len(patient_dict[run]["files"]) )

                            patient_dict[run]["R46"] = np.array(patient_dict[run]["peak_46"]) / np.array(patient_dict[run]["peak_44"])

                            patient_dict[run]["R46_avg"] = patient_dict[run]["R46"].mean()
                            patient_dict[run]["R46_avg_err"] = np.sqrt( patient_dict[run]["R46"].var() / len(patient_dict[run]["files"]) )
                            # n_spectra_r46_actual = int(self.n_spectra_r46.text())
                            # step_r46 = int(np.floor(len(patient_dict[run]["R46"]) / n_spectra_r46_actual))
                            # usable_r46 = patient_dict[run]["R46"][::step_r46]
                            # patient_dict[run]["R46_avg"] = usable_r46.mean()
                            # patient_dict[run]["R46_avg_err"] = np.sqrt( usable_r46.var() / len(usable_r46) )

                        except Exception as e:
                            print(f"Error 2: {e.__class__.__name__} - {e}")
                            patient_dict[run]["R45_avg"] = None
                            patient_dict[run]["R45_avg_err"] = None
                            patient_dict[run]["R46_avg"] = None
                            patient_dict[run]["R46_avg_err"] = None

        return update_flag

    def update_results_table(self, keep_state=False):
        print(f"DEBUG UPDATE TABLE")
        current_state = {}
        # autodetected_runs = {
        #     "Pre": [],
        #     "Post": [],
        # }

        if keep_state:
            for r in range(self.results_table.rowCount()):
                run = self.results_table.item(r, self.results_table_columns.index("Run")).text()

                try:
                    ref_state = self.results_table.item(r, self.results_table_columns.index("REF")).checkState()
                except Exception as e:
                    print(f"Error 3: {e.__class__.__name__} - {e}")
                    ref_state = False

                try:
                    pre_state = self.results_table.item(r, self.results_table_columns.index("Pre")).checkState()
                except Exception as e:
                    print(f"Error 3bis: {e.__class__.__name__} - {e}")
                    pre_state = False

                try:
                    post_state = self.results_table.item(r, self.results_table_columns.index("Post")).checkState()
                except Exception as e:
                    print(f"Error 4: {e.__class__.__name__} - {e}")
                    post_state = False

                current_state[run] = {
                    "REF": ref_state,
                    "Pre": pre_state,
                    "Post": post_state
                }

        # autoedetect pre and post run when only 2 runs are selected and the user didn't selected any runs
        # elif not keep_state or current_state=={}:
        #     for r in range(self.results_table.rowCount()):
        #         run = self.results_table.item(r, self.results_table_columns.index("Run")).text()
        #         if "pre" in run.lower():
        #             autodetected_runs["Pre"].append(run)
        #         elif "post" in run.lower():
        #             autodetected_runs["Post"].append(run)


        self.setup_results_table()
        current_patient = self.patient_list.currentText()
        patient_dict = self.DATA_DICT[current_patient]

        for run in patient_dict.keys():
            run_color = self.DATA_DICT[current_patient][run]["color"]
            row_index = self.results_table.rowCount()
            self.results_table.insertRow(row_index)
            for col in self.results_table_columns:
                print(f"DEBUG COL {run} {col}")
                col_index = self.results_table_columns.index(col)
                item = QTableWidgetItem("")
                font = item.font()
                font.setPointSize(GUI_TABLE_FONT_SIZE)
                item.setFont(font)
                current_flags = item.flags()

                if col == "":
                    item.setText("")
                    item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                    r, g, b = run_color
                    item.setBackground( QBrush(QColor(r, g, b)) )
                elif col == "Run":
                    item.setText(run)
                    item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                elif col == "# spectra":
                    n_files = len(patient_dict[run]["files"])
                    item.setText( f"{n_files}" )
                    item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                elif col == "R45":
                    R45_avg = patient_dict[run]["R45_avg"]
                    item.setText(f"{R45_avg:.4e}")
                    item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                elif col == "R46":
                    R46_avg = patient_dict[run]["R46_avg"]
                    item.setText(f"{R46_avg:.4e}")
                    item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                # elif col == "R45_err":
                #     R45_avg_err = patient_dict[run]["R45_avg_err"]
                #     item.setText(f"{R45_avg_err:.1e}")
                #     item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                elif col == "D":
                    D = (patient_dict[run]["R45_avg"] / R45_PDB - 1 ) * (1 + 0.07032) * 1000
                    item.setText(f"{D:.1f}")
                    item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                elif col == "D_err":
                    D_err = patient_dict[run]["R45_avg_err"] * (1 + 0.07032) / R45_PDB * 1000
                    item.setText(f"{D_err:.1f}")
                    item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                elif col == "D_corr":
                    try:
                        run_46 = patient_dict[run]["R46_avg"]
                        run_corrective_factor = self.reference_46 / run_46
                    except Exception as e:
                        print(f"Err corr: {e.__class__.__name__} - {e}")
                        run_corrective_factor = 1
                    D_corr = (patient_dict[run]["R45_avg"] * run_corrective_factor / R45_PDB - 1) * (1 + 0.07032) * 1000
                    item.setText(f"{D_corr:.1f}")
                    item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                elif col == "D_corr_err":
                    try:
                        run_46 = patient_dict[run]["R46_avg"]
                        run_corrective_factor = self.reference_46 / run_46
                    except Exception as e:
                        print(f"Err corr: {e.__class__.__name__} - {e}")
                        run_corrective_factor = 1
                    D_corr_err = patient_dict[run]["R45_avg_err"] * run_corrective_factor * (1 + 0.07032) / R45_PDB * 1000
                    item.setText(f"{D_corr_err:.1f}")
                    item.setFlags(current_flags & ~Qt.ItemIsEnabled)
                elif col == "REF":
                    if keep_state:
                        state = current_state[run][col]
                    else:
                        state = Qt.CheckState.Unchecked
                    try:
                        item.setCheckState(state)
                    except Exception as e:
                        print(f"Error 5: {e.__class__.__name__} - {e}")
                        item.setCheckState(Qt.CheckState.Unchecked)
                    item.setFlags(current_flags & ~Qt.ItemIsSelectable)
                elif col in ("Pre", "Post"):
                    if keep_state:
                        state = current_state[run][col]
                    else:
                        state = Qt.CheckState.Unchecked
                    try:
                        item.setCheckState(state)
                    except Exception as e:
                        print(f"Error 5 bis: {e.__class__.__name__} - {e}")
                        item.setCheckState(Qt.CheckState.Unchecked)

                    item.setFlags(current_flags & ~Qt.ItemIsSelectable)

                self.results_table.setItem(row_index, col_index, item)

        self.results_table.resizeColumnsToContents()

    def update_plot(self, force_show_all=False):
        self.plot_widget.clear()
        plot_item = self.plot_widget.getPlotItem()

        tick_font = QFont()

        tick_font.setPixelSize(GUI_FONT_SIZE)
        plot_item.getAxis("bottom").setStyle(tickFont=tick_font)
        plot_item.getAxis("bottom").setTextPen('black')
        plot_item.getAxis("left").setStyle(tickFont=tick_font)
        plot_item.getAxis("left").setTextPen('black')
        symbol_size = 10

        pre_index = self.results_table_columns.index("Pre")
        post_index = self.results_table_columns.index("Post")

        if "spectrum" not in  self.plot_type_list.currentText():
            plot_item.setTitle(f"")

            plot_item.showGrid(x=True, y=True)

            for r in range(self.results_table.rowCount()):
                current_patient = self.patient_list.currentText()
                patient_dict = self.DATA_DICT[current_patient]
                run = self.results_table.item(r, self.results_table_columns.index("Run")).text()
                run_color = self.DATA_DICT[current_patient][run]["color"]


                try:
                    pre_selected = self.results_table.item(r, pre_index).checkState() == Qt.CheckState.Checked
                except Exception as e:
                    # print(f"Error 5 tre: {e.__class__.__name__} - {e}")
                    pre_selected = False

                try:
                    post_selected = self.results_table.item(r, post_index).checkState() == Qt.CheckState.Checked
                except:
                    post_selected = False

                selected_state =  pre_selected or post_selected

                if selected_state or force_show_all:
                    n_spectra = len(patient_dict[run]['files'])
                    values_44 = np.array(patient_dict[run]["peak_44"])
                    values_45 = np.array(patient_dict[run]["peak_45"])
                    values_46 = np.array(patient_dict[run]["peak_46"])
                    R45 = np.array(patient_dict[run]["R45"])
                    R46 = np.array(patient_dict[run]["R46"])
                    deltaC = (R45 / R45_PDB - 1 ) * (1 + 0.07032) * 1000
                    deltaC_avg = (patient_dict[run]["R45_avg"] / R45_PDB - 1 ) * (1 + 0.07032) * 1000

                    source_pressures = np.array(patient_dict[run]["source_pressure"])
                    x = list(range(n_spectra))

                    pen = pg.mkPen(color=run_color, width=2)

                    try:

                        if self.plot_type_list.currentText() == "Peak 44":
                            patient_dict[run]["plot_44"] = self.plot_widget.plot(
                                x,
                                values_44,
                                name=f"{run}",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )

                        elif self.plot_type_list.currentText() == "Peak 45":
                            patient_dict[run]["plot_45"] = self.plot_widget.plot(
                                x,
                                values_45,
                                name=f"{run}",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )

                        elif self.plot_type_list.currentText() == "R45":
                            patient_dict[run]["plot_R45"] = self.plot_widget.plot(
                                x,
                                R45,
                                name=f"{run}",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush = run_color,
                                symbolPen=None,
                            )

                            self.plot_widget.plot(
                                (x[0], x[-1]),
                                (patient_dict[run]["R45_avg"], patient_dict[run]["R45_avg"]) ,
                                name=f"{run}_avg",
                                pen=pen,
                                # symbol='o',
                                # symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )

                        elif self.plot_type_list.currentText() == "Peak 46":
                            patient_dict[run]["plot_46"] = self.plot_widget.plot(
                                x,
                                values_46,
                                name=f"{run}",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )


                        elif self.plot_type_list.currentText() == "R46":
                            patient_dict[run]["plot_R46"] = self.plot_widget.plot(
                                x,
                                R46,
                                name=f"{run}",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush = run_color,
                                symbolPen=None,
                            )

                            self.plot_widget.plot(
                                (x[0], x[-1]),
                                (patient_dict[run]["R46_avg"], patient_dict[run]["R46_avg"]) ,
                                name=f"{run}_avg",
                                pen=pen,
                                # symbol='o',
                                # symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )

                        # elif self.plot_type_list.currentText() == "R45 - evolving average":
                        #
                        #     R45_evolving_average = []
                        #     # R45_evolving_average_err = []
                        #
                        #     for i in range(len(x)):
                        #         pass
                        #         partial_data = np.array(R45[:i+1])
                        #         average_partial = partial_data.mean()
                        #         # average_partial_err = np.sqrt( partial_data.var() / len(partial_data) )
                        #         R45_evolving_average.append(average_partial)
                        #         # R45_evolving_average_err.append(average_partial_err)
                        #
                        #     err_plot = self.plot_widget.plot(
                        #         x,
                        #         R45_evolving_average,
                        #         name=f"{run}",
                        #         pen=pen,
                        #         symbol='o',
                        #         symbolSize=symbol_size,
                        #         symbolBrush = run_color,
                        #         symbolPen=None,
                        #     )

                            # error_bars = pg.ErrorBarItem(x=x, y=R45_evolving_average, top=R45_evolving_average_err, bottom=R45_evolving_average_err, beam=0.5)
                            # err_plot.addItem(error_bars)

                        elif self.plot_type_list.currentText() == "Peaks normalized":
                            self.plot_widget.plot(
                                x,
                                values_44 / values_44[0],
                                name=f"{run}_44_norm",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )

                            run_color_45 = tuple(max(x-75, 0) for x in run_color)
                            self.plot_widget.plot(
                                x,
                                values_45 / values_45[0],
                                name=f"{run}_45_norm",
                                pen=pen,
                                symbol='t',
                                symbolSize=symbol_size,
                                symbolBrush=run_color_45,
                                symbolPen=None,
                            )

                            run_color_46 = tuple(max(x-150, 0) for x in run_color)
                            self.plot_widget.plot(
                                x,
                                values_46 / values_46[0],
                                name=f"{run}_46_norm",
                                pen=pen,
                                symbol='t',
                                symbolSize=symbol_size,
                                symbolBrush=run_color_46,
                                symbolPen=None,
                            )

                        # elif self.plot_type_list.currentText() == "bkg - R45":
                        #     self.plot_widget.plot(
                        #         range(len(np.array(patient_dict[run]["background_R45"]))),
                        #         np.array(patient_dict[run]["background_R45"]),
                        #         name=f"{run}",
                        #         pen=pen,
                        #         symbol='o',
                        #         symbolSize=symbol_size,
                        #         symbolBrush=run_color,
                        #         symbolPen=None,
                        #     )
                        #
                        # elif self.plot_type_list.currentText() == "bkg - peak 44":
                        #     self.plot_widget.plot(
                        #         range(len(np.array(patient_dict[run]["background_peak_44"]))),
                        #         np.array(patient_dict[run]["background_peak_44"]),
                        #         name=f"{run}",
                        #         pen=pen,
                        #         symbol='o',
                        #         symbolSize=symbol_size,
                        #         symbolBrush=run_color,
                        #         symbolPen=None,
                        #     )
                        #
                        # elif self.plot_type_list.currentText() == "bkg - peak 45":
                        #     self.plot_widget.plot(
                        #         range(len(np.array(patient_dict[run]["background_peak_45"]))),
                        #         np.array(patient_dict[run]["background_peak_45"]),
                        #         name=f"{run}",
                        #         pen=pen,
                        #         symbol='o',
                        #         symbolSize=symbol_size,
                        #         symbolBrush=run_color,
                        #         symbolPen=None,
                        #     )

                        elif self.plot_type_list.currentText() == "DeltaC":
                            patient_dict[run]["plot_DeltaC"] = self.plot_widget.plot(
                                x,
                                deltaC,
                                name=f"{run}",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush = run_color,
                                symbolPen=None,
                            )

                            self.plot_widget.plot(
                                (x[0], x[-1]),
                                (deltaC_avg, deltaC_avg) ,
                                name=f"{run}_D_avg",
                                pen=pen,
                                # symbol='o',
                                # symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )

                        elif self.plot_type_list.currentText() == "DeltaC - evolving average":
                            deltaC_evolving_average = []
                            for i in range(len(x)):
                                pass
                                partial_data = deltaC[:i+1]
                                average_partial = partial_data.mean()
                                deltaC_evolving_average.append(average_partial)

                            err_plot = self.plot_widget.plot(
                                x,
                                deltaC_evolving_average,
                                name=f"{run}",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush = run_color,
                                symbolPen=None,
                            )


                        elif self.plot_type_list.currentText() == "Source pressure":
                            self.plot_widget.plot(
                                x,
                                source_pressures,
                                name=f"{run}_source_pressure",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )

                        elif self.plot_type_list.currentText() == "peak_44 / pressure":
                            self.plot_widget.plot(
                                x,
                                values_45 / source_pressures,
                                name=f"{run}_source_pressure",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )


                        elif self.plot_type_list.currentText() == "R45 - distribution":
                            bins = np.arange(0.0111, 0.013, 0.0002)
                            R45_hist = np.histogram(R45, bins)

                            self.plot_widget.plot(
                                R45_hist[0],
                                R45_hist[1],
                                name=f"{run}_R45_dist",
                                pen=pen,
                                symbol='o',
                                symbolSize=symbol_size,
                                symbolBrush=run_color,
                                symbolPen=None,
                            )

                    except Exception as e:
                        print(f"No data to plot: {e.__class__.__name__} - {e}")
                        pass

        elif self.plot_type_list.currentText() in ("spectrum - full", "spectrum" ):
            try:
                spectrum_color = (10, 40, 200)
                spectrum_pen = pg.mkPen(color=spectrum_color, width=2)

                self.plot_widget.plot(
                    self.last_spectrum.mass_array,
                    self.last_spectrum.serial_values_array,
                    name=f"Last acquired spectrum",
                    pen=spectrum_pen,
                    symbol='o',
                    symbolSize=symbol_size,
                    symbolBrush = spectrum_color,
                    symbolPen=None,
                )


                spectrum_name = self.last_spectrum.file_name
                plot_item.setTitle(f"<b>{spectrum_name}</b>")
                font = QFont()
                font.setPixelSize(GUI_FONT_SIZE)
                plot_item.getAxis("bottom").setStyle(tickFont = font)
                plot_item.getAxis("bottom").setTextPen('black')

                plot_item.showGrid(x=True, y=True)

                if self.reference_spectrum is not None:
                    reference_spectrum_color = (254, 153, 0)
                    reference_spectrum_pen = pg.mkPen(color=reference_spectrum_color, width=2)

                    self.plot_widget.plot(
                        self.reference_spectrum.mass_array,
                        self.reference_spectrum.serial_values_array,
                        name=f"Reference spectrum",
                        pen=reference_spectrum_pen,
                        symbol='o',
                        symbolSize=symbol_size,
                        symbolBrush = reference_spectrum_color,
                        symbolPen=None,
                    )

            except Exception as e:
                print(f"Error when plotting the spectrum: {e.__class__.__name__} - {e}")
                pass


    def update_dob_result(self):
        # self.dob_label.setFixedSize(  QSize( self.results_table_tot_width, 190) )
        pre_values = []
        pre_values_err = []
        post_values = []
        post_values_err = []

        pre_values_corr = []
        pre_values_err_corr = []
        post_values_corr = []
        post_values_err_corr = []
        for r in range(self.results_table.rowCount()):
            # try:
            #     pre_index = self.results_table_columns.index("Pre")
            #     post_index = self.results_table_columns.index("Post")
            #     R45_index = self.results_table_columns.index("R45")
            #     R45_err_index = self.results_table_columns.index("R45_err")
            #     R46_index = self.results_table_columns.index("R46")
            #     R46_err_index = self.results_table_columns.index("R46_err")
            #
            #     try:
            #         post_state = self.results_table.item(r, post_index).checkState()
            #     except Exception as e:
            #         print(f"Sub error found 2: {e.__class__.__name__} - {e} ROW {r}")
            #         post_state = Qt.CheckState.Unchecked
            #     try:
            #         pre_state = self.results_table.item(r, pre_index).checkState()
            #     except Exception as e:
            #         print(f"Sub error found 1: {e.__class__.__name__} - {e}")
            #         pre_state = Qt.CheckState.Unchecked
            #
            #
            #     if pre_state == Qt.CheckState.Checked:
            #         value = float(self.results_table.item(r, R45_index).text())
            #         err = float(self.results_table.item(r, R45_err_index).text())
            #         pre_values.append(value)
            #         pre_values_err.append(err)
            #
            #     if post_state == Qt.CheckState.Checked:
            #         value = float(self.results_table.item(r, R45_index).text())
            #         err = float(self.results_table.item(r, R45_err_index).text())
            #         post_values.append(value)
            #         post_values_err.append(err)
            #
            # except Exception as e:
            #     print(f"Error found: {e.__class__.__name__} - {e}")
            #     pass

            try:
                pre_index = self.results_table_columns.index("Pre")
                post_index = self.results_table_columns.index("Post")
                D_index = self.results_table_columns.index("D")
                D_err_index = self.results_table_columns.index("D_err")
                D_index_corr = self.results_table_columns.index("D_corr")
                D_err_index_corr = self.results_table_columns.index("D_corr_err")

                try:
                    post_state = self.results_table.item(r, post_index).checkState()
                except Exception as e:
                    print(f"Sub error found 2: {e.__class__.__name__} - {e} ROW {r}")
                    post_state = Qt.CheckState.Unchecked
                try:
                    pre_state = self.results_table.item(r, pre_index).checkState()
                except Exception as e:
                    print(f"Sub error found 1: {e.__class__.__name__} - {e}")
                    pre_state = Qt.CheckState.Unchecked

                if pre_state == Qt.CheckState.Checked:
                    value = float(self.results_table.item(r, D_index).text())
                    err = float(self.results_table.item(r, D_err_index).text())
                    pre_values.append(value)
                    pre_values_err.append(err)

                    value_corr = float(self.results_table.item(r, D_index_corr).text())
                    err_corr = float(self.results_table.item(r, D_err_index_corr).text())
                    pre_values_corr.append(value_corr)
                    pre_values_err_corr.append(err_corr)

                if post_state == Qt.CheckState.Checked:
                    value = float(self.results_table.item(r, D_index).text())
                    err = float(self.results_table.item(r, D_err_index).text())
                    post_values.append(value)
                    post_values_err.append(err)

                    value_corr = float(self.results_table.item(r, D_index_corr).text())
                    err_corr = float(self.results_table.item(r, D_err_index_corr).text())
                    post_values_corr.append(value_corr)
                    post_values_err_corr.append(err_corr)

            except Exception as e:
                print(f"Error found: {e.__class__.__name__} - {e}")
                pass

        if len(pre_values) > 0 and len(post_values) > 0:

            self.pre_avg = np.array(pre_values).mean()
            self.pre_avg_corr = np.array(pre_values_corr).mean()
            try:
                self.pre_avg_err = np.sqrt( (np.array(pre_values_err)**2).sum() / len(pre_values_corr) )
                self.pre_avg_err_corr = np.sqrt( (np.array(pre_values_err_corr)**2).sum() / len(pre_values_corr) )
            except Exception as e:
                print(f"Error: {e.__class__.__name__} - {e}")
                self.pre_avg_err = 0
                self.pre_avg_err_corr = 0

            self.post_avg = np.array(post_values).mean()
            self.post_avg_corr = np.array(post_values_corr).mean()
            try:
                self.post_avg_err = np.sqrt( (np.array(post_values_err)**2).sum() / len(post_values_corr) )
                self.post_avg_err_corr = np.sqrt( (np.array(post_values_err_corr)**2).sum() / len(post_values_corr) )
            except Exception as e:
                print(f"Error: {e.__class__.__name__} - {e}")
                self.post_avg_err = 0
                self.post_avg_err_corr = 0

            # self.delta_R45 =  self.post_avg - self.pre_avg
            # self.delta_R45_err =  np.sqrt( (self.post_avg_err**2 + self.pre_avg_err**2))

            # # self.DOB = (self.post_avg - self.pre_avg) * (1 + 0.07032) / R45_PDB * 1000
            # self.DOB = self.delta_R45 * (1 + 0.07032) / R45_PDB * 1000
            # self.DOB_err = self.delta_R45_err / self.delta_R45 * self.DOB

            self.DOB = self.post_avg - self.pre_avg
            self.DOB_err = np.sqrt( (self.post_avg_err**2 + self.pre_avg_err**2))

            self.DOB_corr = self.post_avg_corr - self.pre_avg_corr
            self.DOB_err_corr = np.sqrt( (self.post_avg_err_corr**2 + self.pre_avg_err_corr**2))

            # print(f"R45 pre: {self.pre_avg:0.4e} +- {self.pre_avg_err:0.4e}")
            # print(f"R45 post: {self.post_avg:0.4e} +- {self.post_avg_err:0.4e}")
            # print(f"Delta R45: {self.delta_R45:0.4e} +- {self.delta_R45_err:0.4e}")
            print(f"DOB: {self.DOB} +- {self.DOB_err}")
            self.dob_label.setText(f"<b>DOB</b><br>{self.DOB:0.2f} +- {self.DOB_err:0.2f}")
            print(f"DOB corrected: {self.DOB_corr} +- {self.DOB_err_corr}")
            DOB_str = f"<b>DOB</b><br>{self.DOB:0.2f} +- {self.DOB_err:0.2f}"
            DOB_corr_str = f"<b>DOB corrected</b><br>{self.DOB_corr:0.2f} +- {self.DOB_err_corr:0.2f}"
            # self.dob_label.setText(f"<b>DOB</b><br>{self.DOB:0.2f} +- {self.DOB_err:0.2f}")
            self.dob_label.setText(f"{DOB_str}<br>{DOB_corr_str}")
            self.DOB = None
            self.DOB_corr = None
        elif len(pre_values) > 0 and len(post_values) == 0:
            self.dob_label.setText(f"Missing post-pill data")
            self.pre_avg = np.array(pre_values).mean()
            self.post_avg = None
            self.DOB = None
            self.DOB_corr = None
        elif len(pre_values) == 0 and len(post_values) > 0:
            self.dob_label.setText(f"Missing pre-pill data")
            self.pre_avg = None
            self.post_avg =  np.array(post_values).mean()
            self.DOB = None
            self.DOB_corr = None
        else :
            self.dob_label.setText(f"Missing pre-pill data<br>Missing post-pill data")
            self.pre_avg = None
            self.post_avg = None
            self.DOB = None
            self.DOB_corr = None


    def results_table_cell_changed(self, row, col):

        if(
            col == self.results_table_columns.index("Pre")
            or col == self.results_table_columns.index("Post")
        ):
            print()

            try:
                # check that all the column for pre and post selection have been created
                pre_index = self.results_table_columns.index("Pre")
                post_index = self.results_table_columns.index("Post")
                self.results_table.item(row, pre_index).checkState()
                self.results_table.item(row, post_index).checkState()
                self.update_dob_result()
            except:
                pass

            force_show_all = True if (self.pre_avg==None and self.post_avg==None) else False
            self.update_plot(force_show_all=force_show_all)

    def reset_reference_selection(self):
        ref_index = self.results_table_columns.index("REF")
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, ref_index)
            item.setCheckState(Qt.CheckState.Unchecked)

    def update_reference_46(self):
        ref_index = self.results_table_columns.index("REF")
        index_46 = self.results_table_columns.index("R46")
        for row in range(self.results_table.rowCount()):
            item_ref = self.results_table.item(row, ref_index)
            item_46 = self.results_table.item(row, index_46)
            if item_ref.checkState() == Qt.CheckState.Checked:
                try:
                    self.reference_46 = float(item_46.text())
                except:
                    self.reference_46 = None

                break

    def results_table_cell_changed_by_user(self, row, col):
        if (
                col == self.results_table_columns.index("REF")
        ):
            try:
                self.reset_reference_selection()
                item = self.results_table.item(row, col)
                item.setCheckState(Qt.CheckState.Checked)
                self.update_reference_46()
            except:
                self.reference_46 = None
                pass

            self.update_results_table(keep_state=True)
            self.update_dob_result()
            force_show_all = True if (self.pre_avg == None and self.post_avg == None) else False
            self.update_plot(force_show_all=force_show_all)


### RUN APP
app = QApplication(sys.argv)
w = MainWindow()
w.setWindowTitle("NTA - Helicobacter")
w.show()
sys.exit(app.exec())