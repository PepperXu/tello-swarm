import threading
# import queue
from djitellopy import TelloSwarm, communication
import time
import json
import socket
import cv2

HOST = '127.0.0.1'
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_address = None

starting_swarm = TelloSwarm.fromIps([
    "192.168.1.65",
    "192.168.1.62",
])

stream_started = False

def receive_messages():
    while True:
        data, addr = server_socket.recvfrom(1024)
        message = data.decode('utf-8')
        print(f"[RECV] From {addr}: {message}")
        global client_address
        client_address = addr
            
        if len(communication.connected_tellos) > 0:
            comp = message.split(" ")
            cur_ip = comp[0]
            cur_command = comp[1]
            process_command(cur_ip, cur_command)
            

def send_server_messages():
    while True:
        if len(communication.message_queue) > 0:
            message = communication.message_queue.pop()
            server_socket.sendto(message.encode('utf-8'), client_address)
            print(f"[SEND] To {HOST}: {message}")
        

def update_status_messages():
    while True:
        if len(communication.connected_tellos) > 0 and client_address:
            for tello in communication.connected_tellos:
                a = {"ip":tello.address[0], "isFlying":tello.is_Flying, "battery":tello.get_battery(), "height":tello.get_height()}
                message = "Status|" + json.dumps(a)
                communication.message_queue.append(message)
        time.sleep(2)
                        

def process_command(ip : str, command:str):
    for tello in communication.connected_tellos:
        if ip == tello.address[0]:
            match command:
                case "takeoff":
                    tello.takeoff()
                case "land":
                    tello.land()

def initialize_server():
    server_socket.bind((HOST, PORT))
    print(f"UDP Server running on {HOST}:{PORT}")


initialize_server()

starting_swarm.connect()
# Start threads
recv_thread = threading.Thread(target=receive_messages, daemon=True)
send_thread = threading.Thread(target=send_server_messages, daemon=True)
update_status_thread = threading.Thread(target=update_status_messages, daemon=True)

recv_thread.start()
send_thread.start()
update_status_thread.start()


# Keep the main thread alive

while True:
    pass