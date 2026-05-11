#JSON commander script provided by Fraunhofer IPM
import socket
import json

def send_commands(cmds, routing, host="127.0.0.1", port=44444):

    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((host, port))

    for cmd in cmds:
        cmd["routing"] = routing
        cmd_string = json.dumps(cmd) + "\n"
        client_socket.send(cmd_string.encode())
        response_string = client_socket.recv(1024).decode()
        
        response = json.loads(response_string)
        if not response["success"]:
            print("Command Failed!")
            print(response_string)
            client_socket.close()
            return
        
        print("Server response:", response)


    # Close the socket
    client_socket.close()