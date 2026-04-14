import os
import numpy as np
import pandas as pd
import laspy as lp
from numpy.polynomial.polynomial import Polynomial
from scipy.interpolate import interp1d
from scipy.spatial.transform import Rotation
from copy import deepcopy
from pathlib import Path

np.set_printoptions(precision=20, suppress=True)
pd.set_option('display.float_format', '{:.6f}'.format)

input_las_file                   = R"Enter_LAS_File_Path"
input_pulsalyzer_trajectory_file = R"Enter_Trajectory_File_Path"

x_rot  = 0
y_rot = 0
z_rot   = 0

chunk_size = 1000000

file_path    = os.path.dirname(os.path.abspath(input_las_file))
las_file_name = Path(input_las_file).stem

output_las_file = os.path.join(file_path, f"python_transformed_{x_rot}_{y_rot}_{z_rot}_{las_file_name}.las")


def interpolate_trajectory(time_traj, x_traj, y_traj, z_traj, tolerance=0.999):

    p = Polynomial.fit(x_traj, y_traj, 1).convert()
    c, m = p.coef
    y_pred = m * x_traj + c
    ss_res = np.sum((y_traj - y_pred) ** 2)
    ss_tot = np.sum((y_traj - np.mean(y_traj)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 1

    print(f"R² : {r_squared:.10f}")
    print(f"Line equation : y = {m:.6f}*x + {c:.6f}\n")

    if r_squared < tolerance:
        raise SystemExit(f"Error: Trajectory is not linear (R² = {r_squared:.6f} < {tolerance}). Stopping.")

    print("Trajectory is linear. Proceeding with linear interpolation.\n")

    f_x = interp1d(time_traj, x_traj, kind='linear')
    f_y = interp1d(time_traj, y_traj, kind='linear')
    f_z = interp1d(time_traj, z_traj, kind='linear')
    return f_x, f_y, f_z


def build_rotation_matrix(x_rot, y_rot, z_rot):

    print(f"Applying XYZ Intrinsic Rotation for angles (X={x_rot}°, Y={y_rot}°, Z={z_rot}°)")
    r = Rotation.from_euler('XYZ', [x_rot, y_rot, z_rot], degrees=True)

    return r.as_matrix()


def transform_chunk(chunk, R, f_x, f_y, f_z):

    timestamps = chunk.gps_time

    x_interp = f_x(timestamps)
    y_interp = f_y(timestamps)
    z_interp = f_z(timestamps)

    points_local   = np.column_stack([chunk.x, chunk.y, chunk.z])
    points_rotated = (R @ points_local.T).T

    chunk.x = points_rotated[:, 0] + x_interp
    chunk.y = points_rotated[:, 1] + y_interp
    chunk.z = points_rotated[:, 2] + z_interp

    return chunk


def apply_compensation_to_las(input_las_file, output_las_file,
                               x_rot, y_rot, z_rot,
                               trajectory_df,
                               chunk_size):
    
    with lp.open(input_las_file) as gps_reader:
        las_gps_limits = []
        for chunk in gps_reader.chunk_iterator(chunk_size):
            las_gps_limits.append([chunk.gps_time.min(), chunk.gps_time.max()])

    las_gps_limits = np.array(las_gps_limits)
    gps_limit_min = las_gps_limits[:, 0].min()
    gps_limit_max = las_gps_limits[:, 1].max()

    if gps_limit_min < trajectory_df['time'].min() or gps_limit_max > trajectory_df['time'].max():
        raise SystemExit(
            f"Error: LAS GPS time [{gps_limit_min:.6f}, {gps_limit_max:.6f}] "
            f"exceeds trajectory [{trajectory_df['time'].min():.6f}, {trajectory_df['time'].max():.6f}]"
        )
    else:
        print(f"LAS GPS limits: {gps_limit_min:.6f} - {gps_limit_max:.6f}")
        print("Filtering trajectory...\n")

        rows_before = trajectory_df[trajectory_df['time'] < gps_limit_min]
        rows_after = trajectory_df[trajectory_df['time'] > gps_limit_max]
        rows_within = trajectory_df[(trajectory_df['time'] >= gps_limit_min) & (trajectory_df['time'] <= gps_limit_max)]
        start_index = rows_before.tail(1)
        end_index = rows_after.head(1)
        filtered_trajectory_df = pd.concat([start_index, rows_within, end_index])

        print(f"Trajectory points after filtering: {len(filtered_trajectory_df)}")
        print(f"Trajectory limits: {filtered_trajectory_df['time'].min():.6f} - {filtered_trajectory_df['time'].max():.6f}\n")


    print(f"Interpolating trajectory...\n")
    f_x, f_y, f_z = interpolate_trajectory(filtered_trajectory_df['time'].values, filtered_trajectory_df['x'].values, filtered_trajectory_df['y'].values, filtered_trajectory_df['z'].values)

    R_mat = build_rotation_matrix(x_rot, y_rot, z_rot)
    print(f"Rotation matrix for (X={x_rot}°, Y={y_rot}°, Z={z_rot}°):\n")
    print(R_mat)

    with lp.open(input_las_file) as reader:
        writer_header = deepcopy(reader.header)
        writer_header.offsets = np.array([filtered_trajectory_df['x'].mean(), filtered_trajectory_df['y'].mean(), filtered_trajectory_df['z'].mean()])
        total_points = reader.header.point_count
        print(f"\nInput LAS file: {input_las_file}")
        print(f"Total points: {total_points}")
        print(f"Chunk size: {chunk_size} points per iteration\n")
        print("Transforming point cloud...\n")

        with lp.open(output_las_file, mode='w', header=writer_header) as writer:
            points_processed = 0

            for chunk in reader.chunk_iterator(chunk_size):
                chunk = transform_chunk(chunk, R_mat, f_x, f_y, f_z)
                writer.write_points(chunk)
                points_processed += len(chunk)
                print(f"Progress: {points_processed}/{total_points} points ({(points_processed/total_points)*100:.1f}%)", end='\r')


    print(f"\nTransformed point cloud saved to : {output_las_file}")
    print(f"{points_processed} points written\n")


print(f"\nLoading trajectory from {input_pulsalyzer_trajectory_file}\n")

trajectory_df = pd.read_csv(input_pulsalyzer_trajectory_file, delimiter='\t')
initial_count = len(trajectory_df)
trajectory_df = trajectory_df.drop_duplicates(subset='time', keep='first')
print(f"Duplicate timestamps removed : {initial_count - len(trajectory_df)}\n")
print(f"Trajectory points loaded : {len(trajectory_df)}\n")


apply_compensation_to_las(
    input_las_file,
    output_las_file,
    x_rot,
    y_rot,
    z_rot,
    trajectory_df,
    chunk_size
)