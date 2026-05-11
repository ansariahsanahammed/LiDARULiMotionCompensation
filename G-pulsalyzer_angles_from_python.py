from scipy.spatial.transform import Rotation

#This script calculates the equivalent rotation angles for Pulsalyzer from the Python rotation angles

#Define rotation angles in Python (degrees)
X = 2.5
Y = 184
Z = 48

#Define the hidden rotation matrix of Pulsalyzer (Extrinsic XYZ)
R_internal_pulsalyzer = Rotation.from_euler('xyz', [180, 0, 90], degrees=True).as_matrix()

#Obtain rotation matrix from Python rotation angles (Intrinsic XYZ)
R_python = Rotation.from_euler('XYZ', [X, Y, Z], degrees=True).as_matrix()

#Calculation of equivalent rotation matrix for Pulsalyzer
R_user = R_internal_pulsalyzer.T @ R_python

#Extract equivalent rotation angles (degrees) for Pulsalyzer from the rotation matrix obtained previously
angles = Rotation.from_matrix(R_user).as_euler('xyz', degrees=True)

#Print the equivalent rotation angles for Pulsalyzer
print(f"For rotation angles of {X}, {Y}, {Z} in Python,")
print(f"Pulsalyzer angles: rx={angles[0]:.2f}, ry={angles[1]:.2f}, rz={angles[2]:.2f}")