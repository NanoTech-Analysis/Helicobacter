import os
import shutil
import time

source_dir = f"C:/Users/gioel/OneDrive/Desktop/temp/data_sample/4_post_1_backup"
target_dir = f"C:/Users/gioel/OneDrive/Desktop/temp/data_sample/samples/4/post_1"

for f in os.listdir(f"{target_dir}"):
    os.remove(f"{target_dir}/{f}")

for f in os.listdir(f"{source_dir}"):
    shutil.copyfile(f"{source_dir}/{f}", f"{target_dir}/{f}" )
    time.sleep(0.3)