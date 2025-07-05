import threading
# import queue
from djitellopy import TelloSwarm, communication
import time
import json

starting_swarm = TelloSwarm.fromIps([
    "192.168.1.65",
    "192.168.1.62",
])

def receive_messages():
    while True:
        data, addr = communication.server_socket.recvfrom(1024)
        message = data.decode('utf-8')
        print(f"[RECV] From {addr}: {message}")
        communication.client_address = addr
        if message == "swarm connect":
            starting_swarm.connect()
        if len(communication.connected_swarm_IP) > 0:
            comp = message.split(" ")
            cur_ip = comp[0]
            cur_command = comp[1]
            process_command(cur_ip, cur_command)
            
            

def send_status_messages():
    while True:
        if len(communication.connected_swarm_IP) > 0 and communication.client_address:
            for tello in starting_swarm:
                    if tello.TELLO_IP in communication.connected_swarm_IP:
                        a = {"ip":tello.TELLO_IP, "battery":tello.get_battery(), "height":tello.get_height()}
                        message = "Status|" + json.dumps(a)
                        communication.server_socket.sendto(message.encode('utf-8'), communication.client_address)
                        print(f"[SEND] To {communication.HOST}: {message}")
        time.sleep(2)

def process_command(ip : str, command:str):
    for tello in starting_swarm:
        if ip == tello.TELLO_IP and tello.TELLO_IP in communication.connected_swarm_IP:
            match command:
                case "stream_on":
                    tello.stream_on()
                case "takeoff":
                    tello.takeoff()
                case "land":
                    tello.land()


communication.initialize_server()
# Start threads
recv_thread = threading.Thread(target=receive_messages, daemon=True)
send_thread = threading.Thread(target=send_status_messages, daemon=True)

recv_thread.start()
send_thread.start()

# Keep the main thread alive

while True:
    pass