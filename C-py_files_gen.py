import laspy as lp
import numpy as np
import os
from pathlib import Path

#Define path to .las file (e.g.: R"C:\Folder\file.las")
las_file = R"Enter_LAS_File_Path"

las_file_name = Path(las_file).stem
file_path = os.path.dirname(os.path.abspath(las_file))

#Print parent folder path of input file
print(f'file_path: {file_path}')

#Define output file names for 10% and 1% .las and .csv files (Saved to same folder as input file)
Downsampled_file_10 = os.path.join(file_path, f"10%_{las_file_name}.las")
Downsampled_file_1  = os.path.join(file_path, f"1%_{las_file_name}.las")
Downsampled_csv_10  = os.path.join(file_path, f"10%_{las_file_name}.csv")
Downsampled_csv_1   = os.path.join(file_path, f"1%_{las_file_name}.csv")

#Function to downsample .las file by retaining every n_th point (Defined by step_size: 10 = 10% of points, 100 = 1% of points)
def downsample_step_size(input_file, output_file, step_size):

    #Read the input .las file (input_file) using laspy and print number of points
    las = lp.read(input_file)
    print(f"Original number of points: {len(las.points)}")

    #Calculate and print expected number of points after downsampling
    n_downsampled = len(las.points[::step_size])
    print(f"Target downsampled size: {n_downsampled}")

    #Slice the points array with the defined step_size
    las.points = las.points[::step_size].copy()
    print(f"Downsampled number of points: {len(las.points)}")

    #Save the downsampled .las file to output_file path
    las.write(output_file)
    print("Downsampling complete.\n")

#Function to convert .las file to comma delimited .csv file (Contains gps_time, x, y, z in columns)
def pcd_to_csv(las_file, output_csv):

    #Read the input .las file (las_file) using laspy
    las = lp.read(las_file)
    
    #Stack gps_time, x, y, and z columns in a numpy array
    dataset = np.vstack((las.gps_time, las.x, las.y, las.z)).transpose()

    #Save the numpy array to a CSV file (output_csv) with headers
    np.savetxt(output_csv, dataset, delimiter=",", header="gps_time,x,y,z", comments='', fmt=['%.6f', '%.8f', '%.8f', '%.8f'])
    print(f"Saved CSV to: {output_csv}")
    return output_csv

#Downsample to .las files (10% and 1%)
downsample_step_size(las_file, Downsampled_file_10, 10)
downsample_step_size(las_file, Downsampled_file_1, 100)

#Convert Downsampled .las files to .csv files
pcd_to_csv(Downsampled_file_10, Downsampled_csv_10)
pcd_to_csv(Downsampled_file_1, Downsampled_csv_1)