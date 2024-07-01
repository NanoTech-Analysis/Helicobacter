import numpy as np
from datetime import datetime
# from scipy.optimize import curve_fit
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class Peak:
    def __init__(
            self,
            nominal_mass = 0.0,
            empirical_mass = 0.0,
            serial_value = 0.0,
    ):
        self.nominal_mass = nominal_mass
        self.empirical_mass = empirical_mass
        self.serial_value = serial_value

    def __repr__(self):
        return f"nominal mass: {self.nominal_mass} - empirical mass: {self.empirical_mass} - serial value: {self.serial_value}"

    def __str__(self):
        return f"nominal mass: {self.nominal_mass} - empirical mass: {self.empirical_mass} - serial value: {self.serial_value}"



class Spectrum:
    def __init__(
            self,
            file_path,
            expected_compound,
            label = None,
            peaks_value_function = lambda x: x.max(),
    ):
        self.file_path = file_path
        self.file_name = file_path.split("/")[-1]
        self.expected_compound = expected_compound
        self.label = label
        self.peaks_value_function = peaks_value_function

        mass_list = []
        serial_values_list = []
        self.peaks_list = []

        with open(self.file_path,"r") as f:

            # read time
            line = f.readline()
            while len(f.readline().strip()) == 0:
                line = f.readline()
            self.start_time = datetime.strptime(line[:25], "%b %d, %Y  %I:%M:%S %p")

            # read noise floor
            line = f.readline()
            while  line.find("Noise Floor") == -1:
                line = f.readline()
            self.noise_floor = float(line.split(",")[1].strip())

            # read HV
            line = f.readline()
            while  line.find("CEM Voltage") == -1:
                line = f.readline()
            self.hv = float(line.split(",")[1].strip())

            # read filament current
            line = f.readline()
            while  line.find("Filament Current") == -1:
                line = f.readline()
            self.current = float(line.split(",")[1].strip())

            # read source pressure
            line = f.readline()
            while  line.find("Source Pressure") == -1:
                line = f.readline()
            try:
                self.source_pressure = float(line.split(",")[1].strip())
            except:
                self.source_pressure = 0

            # read (mass, serial values) pairs
            line = f.readline()
            while line:
                if len(line.strip()) > 0:
                    if line.strip()[0].isdigit():
                        mass = float(line.split(",")[0].strip())
                        serial_value = float(line.split(",")[1].strip())
                        mass_list.append(mass)
                        serial_values_list.append(serial_value)
                line = f.readline()

        self.mass_array = np.array(mass_list)
        self.serial_values_array = np.array(serial_values_list)

        # find peaks
        for expected_peak in expected_compound.expected_peaks:

            # method 1
            try:
                mass_min = expected_peak.nominal_mass - expected_peak.mass_margin_left
                mass_max = expected_peak.nominal_mass + expected_peak.mass_margin_right
                mass_min_index = np.where(self.mass_array == mass_min)[0][0]
                mass_max_index = np.where(self.mass_array == mass_max)[0][0]
                serial_sub_array = self.serial_values_array[mass_min_index: mass_max_index+1]
                actual_peak_mass_sub_index = serial_sub_array.argmax()
                actual_peak_mass_index = actual_peak_mass_sub_index + mass_min_index
                actual_mass = self.mass_array[actual_peak_mass_index]
                peak_value = self.peaks_value_function(serial_sub_array)
            except Exception as e:
                print(f"Error while evaluating the peak for mass {expected_peak.nominal_mass}: {e.__class__.__name__} - {e}")
                actual_mass = expected_peak.nominal_mass
                peak_value = None


            # method 2
            # if expected_peak.nominal_mass == 44.5 and actual_mass < 44.2:
            #     warning_str = "WARNING"
            # # elif expected_peak.nominal_mass == 45.5 and actual_mass > 45.8:
            # #     warning_str = "WARNING"
            # else:
            #     warning_str = ""
            #
            # print(self.file_name, np.floor(expected_peak.nominal_mass), actual_mass, warning_str)

            # method 3
            # if expected_peak.is_main:
            #     mass_min = expected_peak.nominal_mass - expected_peak.mass_margin_left
            #     mass_max = expected_peak.nominal_mass + expected_peak.mass_margin_right
            #     mass_min_index = np.where(self.mass_array == mass_min)[0][0]
            #     mass_max_index = np.where(self.mass_array == mass_max)[0][0]
            #     serial_sub_array = self.serial_values_array[mass_min_index: mass_max_index+1]
            #     peak_value = serial_sub_array.max()
            #     actual_peak_mass_sub_index = serial_sub_array.argmax()
            #     actual_peak_mass_index = actual_peak_mass_sub_index + mass_min_index
            #     actual_mass = self.mass_array[actual_peak_mass_index]
            #     self.main_peak_actual_mass = actual_mass
            # else:
            #     mass = self.main_peak_actual_mass + 1
            #     mass_index = np.where(self.mass_array == mass )[0][0]
            #     peak_value = self.serial_values_array[mass_index]
            #     actual_mass = mass

            peak = Peak(nominal_mass=expected_peak.nominal_mass, empirical_mass=actual_mass , serial_value=peak_value)
            self.peaks_list.append(peak)

        self.available_peaks_mass = np.array( list(peak.nominal_mass for peak in self.peaks_list) )
        self.available_actual_peaks_mass = np.array( list(peak.empirical_mass for peak in self.peaks_list) )
        self.available_peaks_values = np.array( list(peak.serial_value for peak in self.peaks_list) )


    def plot_full(self, existing_figure = None, plot_figure = True, return_figure=False):
        fig = existing_figure if existing_figure != None else go.Figure()

        fig.add_trace(
            go.Scatter(
                x = self.mass_array,
                y = self.serial_values_array,
                name = f"{self.file_name}" if self.label==None else f"{self.label}",
                mode = "lines+markers",
            )
        )

        if plot_figure:
            fig.show()
        if return_figure:
            return fig

    def plot_peaks(self, existing_figure = None, plot_figure = True, return_figure=False):

        fig = existing_figure if existing_figure != None else make_subplots(rows=1, cols=len(self.available_peaks_mass))

        for peak in self.peaks_list:
            plot_index = np.where(self.available_peaks_mass == peak.nominal_mass)[0][0] + 1
            expected_peak = list(expected_peak for expected_peak in self.expected_compound.expected_peaks if expected_peak.nominal_mass == peak.nominal_mass)[0]
            mass_margin_left = expected_peak.mass_margin_left
            mass_margin_right = expected_peak.mass_margin_right
            mass_min = peak.nominal_mass - mass_margin_left - 0.1
            mass_max = peak.nominal_mass + mass_margin_right + 0.1
            mask = (self.mass_array >= mass_min) & (self.mass_array <= mass_max)

            fig.add_scatter(
                x=self.mass_array[mask],
                y=self.serial_values_array[mask],
                row=1,
                col=plot_index,
                mode="lines+markers",
                name = f"{self.file_name}" if self.label==None else f"{self.label}",
            )

        if plot_figure:
            fig.show()
        if return_figure:
            return fig



















