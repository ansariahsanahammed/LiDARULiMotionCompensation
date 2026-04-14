from scipy.spatial.transform import Rotation

#RotationAnglesInPython
X = 2.5
Y = 184
Z = 48

R_internal_pulsalyzer = Rotation.from_euler('xyz', [180, 0, 90], degrees=True).as_matrix()

R_python = Rotation.from_euler('XYZ', [X, Y, Z], degrees=True).as_matrix()

R_user = R_internal_pulsalyzer.T @ R_python

angles = Rotation.from_matrix(R_user).as_euler('xyz', degrees=True)

print(f"For rotation angles of {X}, {Y}, {Z} in Python,")
print(f"Pulsalyzer angles: rx={angles[0]:.2f}, ry={angles[1]:.2f}, rz={angles[2]:.2f}")