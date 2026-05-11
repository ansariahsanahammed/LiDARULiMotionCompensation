import numpy as np
import pandas as pd
import open3d as o3d
import tkinter as tk
from tkinter import ttk, filedialog
from scipy.interpolate import interp1d
from scipy.spatial.transform import Rotation
import threading

#Function to build rotation matrix from 3 Euler angles (degrees) (Intrinsic XYZ)
def build_rotation_matrix(roll_deg, pitch_deg, yaw_deg):
    r = Rotation.from_euler('XYZ', [roll_deg, pitch_deg, yaw_deg], degrees=True)
    return r.as_matrix()

#Function to load pointcloud and trajectory file (.csv files)
def load_files(pcd_path, traj_path):
    pcd_df = pd.read_csv(pcd_path)
    pcd_df.columns = [c.strip().lower() for c in pcd_df.columns]
    if "gps_time" in pcd_df.columns:
        pcd_df.rename(columns={"gps_time": "time"}, inplace=True)

    traj_df = pd.read_csv(traj_path, sep=r"\s+", engine="python")
    traj_df.columns = [c.strip().lower() for c in traj_df.columns]

    #Validate required columns are present in both files
    for col in ["x", "y", "z", "time"]:
        if col not in pcd_df.columns:
            raise ValueError(f"PCD file missing column: '{col}'. Found: {list(pcd_df.columns)}")
        if col not in traj_df.columns:
            raise ValueError(f"Trajectory file missing column: '{col}'. Found: {list(traj_df.columns)}")

    return pcd_df, traj_df

#Function to transform pointcloud
def transform_pcd(pcd_df, traj_df, roll, pitch, yaw):

    #Extract trajectory timestamps and create interpolation functions
    t_traj = traj_df["time"].values.astype(np.float64)
    tx = interp1d(t_traj, traj_df["x"].values, bounds_error=False, fill_value="extrapolate")
    ty = interp1d(t_traj, traj_df["y"].values, bounds_error=False, fill_value="extrapolate")
    tz = interp1d(t_traj, traj_df["z"].values, bounds_error=False, fill_value="extrapolate")

    #Get timestamps from the pointcloud file and create a translation matrix 
    t_pts = pcd_df["time"].values.astype(np.float64)
    translation = np.column_stack([tx(t_pts), ty(t_pts), tz(t_pts)])

    #Get position information from the pointcloud file
    pts_local = pcd_df[["x", "y", "z"]].values.astype(np.float64)
    #Build the rotation matrix
    R = build_rotation_matrix(roll, pitch, yaw)
    #Transform the pointcloud
    pts_rotated = (R @ pts_local.T).T
    pts_world   = pts_rotated + translation

    #Return the transformed pointcloud
    return pts_world

#Class to handle Open3D visualization in a separate window
class RealtimeVisualiser:

    #Initialise Open3D Visualizer
    def __init__(self):
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(window_name="Boresight Calibration Viewer", width=1100, height=700)
        self.pcd_o3d      = o3d.geometry.PointCloud()
        self.vis.add_geometry(self.pcd_o3d)
        self._add_axes()
        self.needs_update = False
        self._reset_view  = False
        self.new_pts      = None
        self.lock         = threading.Lock()

    #Add axes to the visualization
    def _add_axes(self):
        axes = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0, origin=[0, 0, 0])
        self.vis.add_geometry(axes)

    #Update points to be shown
    def set_points(self, pts, reset_view=False):

        with self.lock:
            self.new_pts      = pts
            self.needs_update = True
            self._reset_view  = reset_view

    #Adjust camera to fit pointcloud
    def _fit_view_to_cloud(self, pts):
        centroid = pts.mean(axis=0)
        extent   = np.ptp(pts, axis=0).max()         
        extent   = max(extent, 1.0)                   

        vc = self.vis.get_view_control()
        vc.set_lookat(centroid.tolist())
        vc.set_zoom(0.5)
        vc.set_front([0.0, 0.0, -1.0])
        vc.set_up([0.0, -1.0, 0.0])

    #Run the visualization
    def spin(self):
        with self.lock:
            if self.needs_update and self.new_pts is not None:
                self.pcd_o3d.points = o3d.utility.Vector3dVector(self.new_pts)
                z       = self.new_pts[:, 2]
                z_range = np.ptp(z)
                z_norm  = (z - z.min()) / (z_range + 1e-9)
                colours = np.column_stack([z_norm, 1 - z_norm, np.zeros_like(z_norm)])
                self.pcd_o3d.colors = o3d.utility.Vector3dVector(colours)
                self.vis.update_geometry(self.pcd_o3d)

                if self._reset_view:
                    self._fit_view_to_cloud(self.new_pts)
                    self._reset_view = False

                self.needs_update = False

        self.vis.poll_events()
        self.vis.update_renderer()

    #Close the window
    def destroy(self):
        self.vis.destroy_window()

#Class to handle the control panel
class ControlPanel:

    #Initialise control panel
    def __init__(self, root, visualiser):
        self.root        = root
        self.vis         = visualiser
        self.pcd_df      = None
        self.traj_df     = None
        self._pcd_path   = None
        self._traj_path  = None
        self._first_apply = True

        #Setup the control panel
        root.title("Boresight Calibration Controls")
        root.resizable(False, False)

        #File selection
        frm_files = ttk.LabelFrame(root, text="Files", padding=8)
        frm_files.grid(row=0, column=0, padx=10, pady=6, sticky="ew")

        self.pcd_var  = tk.StringVar(value="No file selected")
        self.traj_var = tk.StringVar(value="No file selected")

        ttk.Button(frm_files, text="Point Cloud (.csv)",
                   command=self._load_pcd).grid(row=0, column=0, sticky="w")
        ttk.Label(frm_files, textvariable=self.pcd_var, width=48,
                  foreground="grey").grid(row=0, column=1, padx=6)

        ttk.Button(frm_files, text="Trajectory (.txt)",
                   command=self._load_traj).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(frm_files, textvariable=self.traj_var, width=48,
                  foreground="grey").grid(row=1, column=1, padx=6)

        ttk.Button(frm_files, text="Apply & View",
                   command=self._apply).grid(row=2, column=0, columnspan=2, pady=(6, 0))

        #Rotation controls
        frm_rot = ttk.LabelFrame(root, text="Boresight Rotation (degrees)", padding=8)
        frm_rot.grid(row=1, column=0, padx=10, pady=6, sticky="ew")

        self.roll_var  = tk.DoubleVar(value=0.0)
        self.pitch_var = tk.DoubleVar(value=0.0)
        self.yaw_var   = tk.DoubleVar(value=0.0)

        #Create sliders for rotation
        self._make_slider(frm_rot, "Roll  (X)", self.roll_var,  0)
        self._make_slider(frm_rot, "Pitch (Y)", self.pitch_var, 1)
        self._make_slider(frm_rot, "Yaw   (Z)", self.yaw_var,   2)

        ttk.Button(frm_rot, text="Reset Camera View",
                   command=self._reset_cam).grid(row=3, column=0, columnspan=3, pady=(8, 0))

        #File format reference
        frm_info = ttk.LabelFrame(root, text="File Format Reference", padding=6)
        frm_info.grid(row=2, column=0, padx=10, pady=4, sticky="ew")
        ttk.Label(frm_info, text="PCD  (.csv) :  gps_time, x, y, z",
                  font=("Courier", 9)).grid(row=0, column=0, sticky="w")
        ttk.Label(frm_info, text="Traj (.txt) :  time  x  y  z  roll  pitch  yaw",
                  font=("Courier", 9)).grid(row=1, column=0, sticky="w")


        self.status_var = tk.StringVar(value="Load both files then click Apply.")
        ttk.Label(root, textvariable=self.status_var, foreground="blue",
                  wraplength=460).grid(row=3, column=0, padx=10, pady=4)

    #Create a slider with a label and text entry
    def _make_slider(self, parent, label, var, row):
        ttk.Label(parent, text=label, width=10).grid(row=row, column=0, sticky="w")
        sl = ttk.Scale(parent, from_=-180, to=180, orient="horizontal",
                       variable=var, length=280,
                       command=lambda _: self._on_slider())
        sl.grid(row=row, column=1, padx=6)
        entry = ttk.Entry(parent, textvariable=var, width=8)
        entry.grid(row=row, column=2)
        entry.bind("<Return>", lambda _: self._on_slider())
    
    #Open point cloud file
    def _load_pcd(self):
        path = filedialog.askopenfilename(
            title="Select Point Cloud CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self._pcd_path = path
            self.pcd_var.set(path.split("/")[-1])

    #Open trajectory file
    def _load_traj(self):
        path = filedialog.askopenfilename(
            title="Select Trajectory TXT",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self._traj_path = path
            self.traj_var.set(path.split("/")[-1])

    #Load files and update visualization
    def _apply(self):
        if not self._pcd_path or not self._traj_path:
            self.status_var.set("Please select both files first.")
            return
        try:
            self.pcd_df, self.traj_df = load_files(self._pcd_path, self._traj_path)
            self.status_var.set(
                f"Loaded {len(self.pcd_df):,} points  |  "
                f"{len(self.traj_df):,} trajectory epochs.  Adjust sliders to rotate."
            )
            self._first_apply = True
            self._update_vis()
        except Exception as e:
            self.status_var.set(f"Error loading files: {e}")

    #Apply transformation and reset camera view
    def _reset_cam(self):
        if self.pcd_df is not None:
            pts = transform_pcd(self.pcd_df, self.traj_df,
                                self.roll_var.get(),
                                self.pitch_var.get(),
                                self.yaw_var.get())
            self.vis.set_points(pts, reset_view=True)

    #Update visualization when slider is moved
    def _on_slider(self):
        if self.pcd_df is not None:
            self._update_vis()

    #Update visualization with current rotation angles
    def _update_vis(self):
        try:
            pts = transform_pcd(self.pcd_df, self.traj_df,
                                self.roll_var.get(),
                                self.pitch_var.get(),
                                self.yaw_var.get())
            do_reset = self._first_apply
            self._first_apply = False
            self.vis.set_points(pts, reset_view=do_reset)
            self.status_var.set(
                f"Roll={self.roll_var.get():.1f}°  "
                f"Pitch={self.pitch_var.get():.1f}°  "
                f"Yaw={self.yaw_var.get():.1f}°  "
                f"| {len(pts):,} pts"
            )
        except Exception as e:
            self.status_var.set(f"Transform error: {e}")

#Main function
def main():

    #Initialize the visualization and control panel
    vis  = RealtimeVisualiser()
    root = tk.Tk()
    app  = ControlPanel(root, vis)

    #Function to loop the visualization
    def loop():
        vis.spin()
        root.after(30, loop)

    root.after(30, loop)

    try:
        root.mainloop()
    finally:
        vis.destroy()

if __name__ == "__main__":
    main()
