from datetime import datetime, timezone
import math
import numpy as np
import os

#Define base date of scan and orientation offsets of scanner (in degrees)
Year = '2025'
Month = '08'
Day = '06'
x_rot = 0
y_rot = 0
z_rot = 0

#Calculate base timestamp from base date (at 00:00:00 UTC)
base_date = datetime(int(Year), int(Month), int(Day), tzinfo=timezone.utc)
base_timestamp = datetime.timestamp(base_date)

#Define UTC to TAI offset (seconds) and prism to scanner lever arm (meters)
utc2tai_offset = 37
prism_to_scanner_lever_arm = 1.65

#Define input trajectory file path (e.g.: R"C:\Folder\file.txt")
input_trajectory_file = R"Enter_absolute_path_to_trajectory_file"
traj_path = os.path.dirname(os.path.abspath(input_trajectory_file))

#Output trajectory file path (Saved to same folder as input file)
converted_pulsalyzer_trajectory_file = os.path.join(traj_path, f"converted_{Year}_{Month}_{Day}_offset_{utc2tai_offset}_traj_{x_rot}_{y_rot}_{z_rot}.txt")

#Function to calculate final timestamp from time of day (HHMMSS.SSS) added to base timestamp
def new_timestamp(hhmmss, base_ts = base_timestamp):
    hh = hhmmss // 10000
    mm = hhmmss % 10000 // 100
    ss = hhmmss % 100
    total_seconds = (hh * 3600) + (mm * 60) + ss
    time_stamp = base_ts + total_seconds
    return np.round(time_stamp, decimals=6)

#Function to convert trajectory to Pulsalyzer format
def convert_raw_to_pulsalyzer_numpy(input_file):
    
    #Read raw trajectory file (input_file) with column names 'time', 'x', 'y', 'z', 'alpha', 'theta', 'distance'
    raw_names = ['time', 'x', 'y', 'z', 'alpha', 'theta', 'distance']
    traj_data = np.genfromtxt(input_file, names=raw_names, dtype=np.float64)

    gon_to_rad = math.pi / 200.0

    #Extract columns from trajectory
    time_col = traj_data['time']
    alpha_col = traj_data['alpha']
    theta_col = traj_data['theta']
    distance_col = traj_data['distance']

    #Convert angles from Gradians to Radians
    alpha_rad = alpha_col * gon_to_rad
    theta_rad = theta_col * gon_to_rad
    
    #Convert Polar coordinates to Cartesian coordinates
    x_new = np.round(distance_col * np.sin(theta_rad) * np.cos(alpha_rad), 6)
    y_new = np.round(distance_col * np.sin(theta_rad) * np.sin(alpha_rad), 6)
    z_new = np.round(distance_col * np.cos(theta_rad), 6)

    #Convert to right handed coordinate system
    y_new = -y_new

    #Lever arm correction
    z_new = z_new - prism_to_scanner_lever_arm

    #Calculate timestamps from function 'new_timestamp' and add the UTC to TAI offset
    time_col = new_timestamp(time_col) + utc2tai_offset
    
    #Create roll, pitch, yaw columns (constant value of 0)
    num_rows = len(time_col)
    roll_col = np.full(num_rows, x_rot)
    pitch_col = np.full(num_rows, y_rot)
    yaw_col = np.full(num_rows, z_rot)

    #Stack columns as per Pulsalyzer format
    new_traj = np.column_stack((time_col, x_new, y_new, z_new, roll_col, pitch_col, yaw_col))
    trajectory_header = ['time', 'x', 'y', 'z', 'roll', 'pitch', 'yaw']

    return new_traj, trajectory_header

#Print information
print(f"\nUTC to TAI offset: {utc2tai_offset} s\n")
print(f"Prism to scanner lever arm: {prism_to_scanner_lever_arm} m\n")
print(f"Input trajectory file: {input_trajectory_file}\n")
print("Converting to Pulsalyzer format...\n")

#Convert trajectory to Pulsalyzer format and save to defined output path as tab-delimited text file
trajectory_converted, trajectory_header = convert_raw_to_pulsalyzer_numpy(input_trajectory_file)
np.savetxt(converted_pulsalyzer_trajectory_file, trajectory_converted, header='\t'.join(trajectory_header), delimiter='\t', comments='', fmt='%.6f')
print(f"Converted trajectory file: {converted_pulsalyzer_trajectory_file}\n")
