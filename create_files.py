import os
import datetime
import time
import shutil
import random


FILES_SOURCE_DIR = "C:/Users/Carla/OneDrive/Desktop/BOLOGNA/source_files"
template_files = [
    "C:/Users/Carla/OneDrive/Desktop/BOLOGNA/caratterizzazione_proto_3/2024_04_12/samples/2/pre_1/2024_04_12_09_01_05.txt",
    "C:/Users/Carla/OneDrive/Desktop/BOLOGNA/caratterizzazione_proto_3/2024_04_12/samples/2/pre_1/2024_04_12_09_01_10.txt",
    "C:/Users/Carla/OneDrive/Desktop/BOLOGNA/caratterizzazione_proto_3/2024_04_12/samples/2/pre_1/2024_04_12_09_01_14.txt",
    "C:/Users/Carla/OneDrive/Desktop/BOLOGNA/caratterizzazione_proto_3/2024_04_12/samples/2/pre_1/2024_04_12_09_01_19.txt",
    "C:/Users/Carla/OneDrive/Desktop/BOLOGNA/caratterizzazione_proto_3/2024_04_12/samples/2/pre_1/2024_04_12_09_01_24.txt",
    "C:/Users/Carla/OneDrive/Desktop/BOLOGNA/caratterizzazione_proto_3/2024_04_12/samples/2/pre_1/2024_04_12_09_01_28.txt",
    "C:/Users/Carla/OneDrive/Desktop/BOLOGNA/caratterizzazione_proto_3/2024_04_12/samples/2/pre_1/2024_04_12_09_01_33.txt",
]

while True:
    files = os.listdir(FILES_SOURCE_DIR)
    if len(files) < 20:
        random_file = random.choice(template_files)
        name = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        shutil.copy(random_file, f"{FILES_SOURCE_DIR}/{name}.txt")
        time.sleep(1)
    else:
        for f in files:
            os.remove(f"{FILES_SOURCE_DIR}/{f}")