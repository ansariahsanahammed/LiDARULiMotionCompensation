# LiDARULiMotionCompensation

Python workflow for applying **Motion Compensation** and **Boresight Calibration** to LiDAR point clouds acquired with the ULi system. The workflow facilitates the georeferencing of point clouds using a linear trajectory data

Developed as part of a Master Thesis at **HafenCity Universität, Hamburg** titled *"Development and analysis of motion compensation algorithms for the underwater LiDAR ULi"*.

## Requirements

*   **Python**: 3.12.10
*   **laspy**: 2.6.1
*   **numpy**: 2.3.2
*   **open3d**: 0.19.0
*   **pandas**: 2.3.1
*   **scipy**: 1.16.3

## Files included:
- `A-json_commander.py`: For sending commands via JSONServer to Pulsalyzer (provided by Fraunhofer IPM).
- `B-trajectory_conversion.py`: Convert raw trajectory to Pulsalyzer format.
- `C-py_files_gen.py`: Downsample .las files and save as .las and .csv files.
- `D-python_workflow.py`: The Python workflow used for motion compensation.
- `E-boresight_calibration.py`: GUI for real-time boresight calibration using Open3D.
- `F-pulsalyzer_real_time_visualizer.py`: Script to visualise real-time rotations in Pulsalyzer.
- `G-pulsalyzer_angles_from_python.py`: Calculate equivalent rotation angles for Pulsalyzer using angles used in Python workflow.

## Repository Versions

*   **`main` branch**: Contains the updated scripts with comments and organized file naming.
*   **`thesis-submission` branch**: A static snapshot of the original scripts in their exact state at the time of the Master's thesis submission.