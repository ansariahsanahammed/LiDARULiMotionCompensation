import laspy as lp
import numpy as np
import os
from pathlib import Path

las_file = R"Enter_LAS_File_Path"
las_file_name = Path(las_file).stem
file_path = os.path.dirname(os.path.abspath(las_file))

print(f'file_path: {file_path}')

Downsampled_file_10 = os.path.join(file_path, f"10%_{las_file_name}.las")
Downsampled_file_1  = os.path.join(file_path, f"1%_{las_file_name}.las")
Downsampled_csv_10  = os.path.join(file_path, f"10%_{las_file_name}.csv")
Downsampled_csv_1   = os.path.join(file_path, f"1%_{las_file_name}.csv")

def downsample_step_size(input_file, output_file, step_size):

    las = lp.read(input_file)
    print(f"Original number of points: {len(las.points)}")

    n_downsampled = len(las.points[::step_size])
    print(f"Target downsampled size: {n_downsampled}")

    las.points = las.points[::step_size].copy()
    print(f"Downsampled number of points: {len(las.points)}")

    las.write(output_file)
    print("Downsampling complete.\n")

def pcd_to_csv(las_file, output_csv):
    las = lp.read(las_file)
    dataset = np.vstack((las.gps_time, las.x, las.y, las.z)).transpose()
    np.savetxt(output_csv, dataset, delimiter=",", header="gps_time,x,y,z", comments='', fmt=['%.6f', '%.8f', '%.8f', '%.8f'])
    print(f"Saved CSV to: {output_csv}")
    return output_csv

downsample_step_size(las_file, Downsampled_file_10, 10)
downsample_step_size(las_file, Downsampled_file_1, 100)

pcd_to_csv(Downsampled_file_10, Downsampled_csv_10)
pcd_to_csv(Downsampled_file_1, Downsampled_csv_1)