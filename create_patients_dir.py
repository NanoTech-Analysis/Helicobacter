import os
import datetime
from globals import REAL_TIME_MAIN_DIR


N_PATIENTS = 21

date = datetime.datetime.now().date().strftime("%Y_%m_%d")
date_dir = f"{REAL_TIME_MAIN_DIR}/{date}"
# date_dir = f"{REAL_TIME_MAIN_DIR}/2024_06_24"
os.makedirs(f"{date_dir}", exist_ok=True)
os.makedirs(f"{date_dir}/samples", exist_ok=True)
os.makedirs(f"{date_dir}/background", exist_ok=True)
os.makedirs(f"{date_dir}/risultati_bologna", exist_ok=True)

for i in range(N_PATIENTS):
    os.makedirs(f"{date_dir}/samples/{i}", exist_ok=True)
    os.makedirs(f"{date_dir}/samples/{i}/pre_1", exist_ok=True)
    os.makedirs(f"{date_dir}/samples/{i}/post_1", exist_ok=True)

