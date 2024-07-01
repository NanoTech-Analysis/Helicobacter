from pathlib import Path
import openpyxl
import numpy as np
from globals import *
from globals_local_values import *

import plotly.graph_objects as go


DATA_DIR = Path(REAL_TIME_MAIN_DIR)
RESULTS_SHEET_NAME = "pazienti_bologna.xlsx"
RESULTS_SHEET = DATA_DIR / RESULTS_SHEET_NAME

SHEETS_TO_INCLUDE = [
    "esiti - maggio",
    # "esiti - giugno",
]

# COLUMNS MAPPING
DATE_INDEX = 0
PATIENT_N_INDEX = 1
DATE_PATIENT_N_INDEX = 2
SURNAME_INDEX = 3
NAME_INDEX = 4
TRIAL_INDEX = 5
RESULT_INDEX = 6
DOB_OFFICIAL_INDEX = 7
DOB_NANO_INDEX = 14
DOB_NANO_CORRECTED_INDEX = 15
RUN_LABEL_INDEX = 19

PATIENTS_TO_EXCLUDE = {
    "2024_05_20": [2,],
    "2024_05_24": [14,],
    "2024_05_29": list(range(1,13)),
    "2024_05_30": list(range(1, 17)),
    "2024_05_31": list(range(1, 14)),
}

class PatientRun():
    def __init__(self, label, values_44=[], values_45=[], values_46=[]):
        self.label = label
        self.values_44_list = values_44
        self.values_45_list = values_45
        self.values_46_list = values_46

    def get_max_n_spectra(self):
        return min( len(self.values_44_list), len(self.values_45_list), len(self.values_46_list) )

    def get_values_44(self, n_spectra=-1):
        n_spectra = n_spectra if n_spectra>0 and n_spectra<=self.get_max_n_spectra() else self.get_max_n_spectra()
        return np.array(self.values_44_list[:n_spectra])
    
    def get_values_45(self, n_spectra=-1):
        n_spectra = n_spectra if n_spectra>0 and n_spectra<=self.get_max_n_spectra() else self.get_max_n_spectra()
        return np.array(self.values_45_list[:n_spectra])

    def get_values_46(self, n_spectra=-1):
        n_spectra = n_spectra if n_spectra>0 and n_spectra<=self.get_max_n_spectra() else self.get_max_n_spectra()
        return np.array(self.values_46_list[:n_spectra])

    def get_values_R45(self, n_spectra=-1):
        return self.get_values_45(n_spectra) / self.get_values_44(n_spectra)

    def get_values_R46(self, n_spectra=-1):
        return self.get_values_46(n_spectra) / self.get_values_44(n_spectra)

    
    def get_R45(self, n_spectra=-1):
        return self.get_values_R45(n_spectra).mean() if self.get_max_n_spectra()>0 else 0

    
    def get_R46(self, n_spectra=-1):
        return self.get_values_R46(n_spectra).mean() if self.get_max_n_spectra()>0 else 0
    
    def get_values_deltaC13(self, n_spectra=-1):
        return (self.get_values_R45(n_spectra) / R45_PDB - 1) * (1 + 0.07032) * 1000

    def get_deltaC13(self, n_spectra=-1):
        return self.get_values_deltaC13(n_spectra).mean() if self.get_max_n_spectra()>0 else 0

    def __str__(self):
        return f"Run {self.label} - #spectra: {self.get_max_n_spectra()} - R45:{self.get_R45()} - R46:{self.get_R46()} - deltaC13:{self.get_deltaC13()}"

class Patient():
    def __init__(self, patient_n, date, date_patient_n, in_trial, result, dob_official, run_pre_label="", run_post_label=""):
        self.patient_n = patient_n
        self.date = date
        self.date_patient_n = date_patient_n
        self.in_trial = in_trial
        self.result_official = result
        self.dob_official = dob_official
        self.run_pre = PatientRun(run_pre_label)
        self.run_post = PatientRun(run_post_label)
        self.DOB = None
        self.DOB_corrected = None
        self.correction_factor = None
        self.results_database = {}


    def __str__(self):
        return f"Patient #{self.patient_n} {self.date}->{self.date_patient_n} - DOB={self.dob_official} - {self.result_official} - TRIAL={self.in_trial}"

    def load_run_data(self, run_type):
        assert run_type.lower() in ["pre", "post"]
        run = self.run_pre if run_type.lower()=="pre" else self.run_post
        label = run.label
        print(f"Loading data for {self} - {label}")
        for f in (DATA_DIR/self.date/"samples"/str(self.date_patient_n)/label).iterdir():
            lines = f.read_text().split("\n")
            for line in lines:
                if line.strip().split(",")[0].replace(".", "").isnumeric():
                    m = float(line.strip().split(",")[0])
                    value = float(line.strip().split(",")[1])
                    print("DEBUG", run)
                    if m==44:
                        run.values_44_list.append(value)
                    elif m==45:
                        run.values_45_list.append(value)
                    elif m==46:
                        run.values_46_list.append(value)

    def load_data(self):
        self.load_run_data("pre")
        self.load_run_data("post")

    def update_results_database(self):
        self.results_database[self.n_spectra_results] = {
            "DOB": self.DOB,
            "DOB_corrected": self.DOB_corrected,
            "correction_factor": self.correction_factor,
        }

    def compute_results_nanotech(self, n_spectra=-1 ):
        self.n_spectra_results = n_spectra if n_spectra > 0 else len(self.get_values_44())
        self.DOB = self.run_post.get_deltaC13(n_spectra) - self.run_pre.get_deltaC13(n_spectra)
        self.correction_factor = self.run_pre.get_R46(n_spectra) / self.run_post.get_R46(n_spectra)
        self.DOB_corrected = self.run_post.get_deltaC13(n_spectra)*self.correction_factor - self.run_pre.get_deltaC13(n_spectra)
        self.update_results_database()


def read_row(row):
    date = row[DATE_INDEX].value
    patient_n = row[PATIENT_N_INDEX].value
    date_patient_n = row[DATE_PATIENT_N_INDEX].value
    result = row[RESULT_INDEX].value
    dob_official = row[DOB_OFFICIAL_INDEX].value
    run_label = row[RUN_LABEL_INDEX].value
    in_trial_str = row[TRIAL_INDEX].value
    if in_trial_str is not None:
        in_trial = in_trial_str.upper() == "SI"
    else:
        in_trial = None

    return date, patient_n, date_patient_n, result, dob_official, run_label, in_trial


if __name__ == "__main__":
    PATIENTS = []
    WORKBOOK = openpyxl.load_workbook(filename=RESULTS_SHEET)

    # Load the list of patients.
    for sheet in SHEETS_TO_INCLUDE:
        current_patient = None
        for row in list(WORKBOOK[sheet].rows)[2:]:
            date, patient_n, date_patient_n, result, dob_official, run_label, in_trial = read_row(row)
            try:
                if patient_n is not None:
                    current_patient = Patient(patient_n=patient_n,date=date,date_patient_n=date_patient_n,in_trial=in_trial,result=result,dob_official=dob_official,run_pre_label="", run_post_label="")
                    current_patient.run_pre = PatientRun(run_label)
                else:
                    current_patient.run_post = PatientRun(run_label)
                    if current_patient.date_patient_n not in PATIENTS_TO_EXCLUDE.get(current_patient.date, []):
                        PATIENTS.append(current_patient)
                        print(current_patient)

                    else:
                        print(f"{current_patient} -> EXCLUDED")
            except Exception as e:
                current_patient = None
                print(f"Error reading info for patient #{patient_n} {date}->{date_patient_n}: {e.__class__.__name__} - {e}")


    # Load the spectra for each patient
    for patient in PATIENTS:
        print()
        patient.load_data()
        print(patient.run_pre)
        print(patient.run_post)

    #     # for n_spectra in (50, 75, 100):
    #     for n_spectra in (10,):
    #         patient.compute_results_nanotech(n_spectra=n_spectra)
    #         print(patient)
    #         print(patient.run_pre)
    #         print(patient.run_post)







