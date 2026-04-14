import json_commander
from time import sleep
import contextlib
import os

def send_silent(cmd, routing):
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        json_commander.send_commands(cmd, routing)


routing1 = ["PointcloudProcessing", "Pulsalyzer", "DEVICE(HOST)_NAME_OBTAINED_FROM_WEBSERVER"]


x_rot = 0
y_rot = 0
z_rot = 0

start = 0
stop = 10


cmds = []

cmds.append({"cmd": "set_scanner_transformation_deg", "rx": x_rot, "ry": y_rot, "rz": z_rot})
cmds.append({"cmd": "reprocess_pointcloud", "point_step": 5})
cmds.append({"cmd": "redraw_pointcloud", "point_step": 5})


send_silent(cmds, routing1)

input("\nPress Enter\n")
while True:
    for i in range (start, stop + 1, 1):
        x_ang = x_rot
        y_ang = y_rot + i
        z_ang = z_rot
        cmd_loop = [
            {"cmd": "set_scanner_transformation_deg", "rx": x_ang, "ry": y_ang, "rz": z_ang},
            {"cmd": "reprocess_pointcloud", "point_step": 50},
            {"cmd": "redraw_pointcloud", "point_step": 50}
            ]
        send_silent(cmd_loop, routing1)
        print(f"{x_ang}, {y_ang}, {z_ang}")
    print("-----")
print("-----")
