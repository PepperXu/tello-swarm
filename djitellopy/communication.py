import socket

HOST = '127.0.0.1'
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_address = None

connected_swarm_IP = []

def initialize_server():
    server_socket.bind((HOST, PORT))
    print(f"UDP Server running on {HOST}:{PORT}")

def send_response(msg : str):
    if len(connected_swarm_IP) > 0 and client_address:
        server_socket.sendto(msg.encode('utf-8'), client_address)
        print(f"[SEND] To {HOST}: {msg}")

