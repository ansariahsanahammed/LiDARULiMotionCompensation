import json_commander
from time import sleep
import contextlib
import os

#Function to send commands to Pulsalyzer without printing responses to the terminal.
#Keeps the output clean during loops
def send_silent(cmd, routing):
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        json_commander.send_commands(cmd, routing)

#Define routing path to the required endpoint
#Host name can be obtained via the Pulsalyzer WebServer or via the command 'hostname' in Command Prompt
routing1 = ["PointcloudProcessing", "Pulsalyzer", "DEVICE(HOST)_NAME_OBTAINED_FROM_WEBSERVER"]

#Initial rotation angles (degrees)
x_rot = 0
y_rot = 0
z_rot = 0

#Range for the angle to be iterated in the loop
start = 0
stop = 10

#List to hold the commands to be sent
cmds = []

#Commands to transform the pointcloud using the initial rotation angles, and then reprocess and redraw the pointcloud
cmds.append({"cmd": "set_scanner_transformation_deg", "rx": x_rot, "ry": y_rot, "rz": z_rot})
cmds.append({"cmd": "reprocess_pointcloud", "point_step": 5})
cmds.append({"cmd": "redraw_pointcloud", "point_step": 5})

#Send the initial commands to Pulsalyzer endpoint
send_silent(cmds, routing1)

input("\nPress Enter\n")

#Main loop to continuously update the visualization by incrementing angles along one axis
while True:
    for i in range (start, stop + 1, 1): #iterate from start to stop with a step of 1, modify step as necessary
        x_ang = x_rot
        y_ang = y_rot + i #add the increment to the y rotation angle, modify as necessary
        z_ang = z_rot

        #Commands list to update the visualization, speed of update depends on 'point_step' value
        cmd_loop = [
            {"cmd": "set_scanner_transformation_deg", "rx": x_ang, "ry": y_ang, "rz": z_ang},
            {"cmd": "reprocess_pointcloud", "point_step": 50},
            {"cmd": "redraw_pointcloud", "point_step": 50}
            ]

        #Send commands to Pulsalyzer endpoint
        send_silent(cmd_loop, routing1)
        #Print the current rotation angles
        print(f"{x_ang}, {y_ang}, {z_ang}")
    print("-----")
print("-----")
