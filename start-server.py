import threading
# import queue
from djitellopy import TelloSwarm, communication, Tello
import time
import json
import socket

HOST = '127.0.0.1'
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_address = None

starting_swarm = TelloSwarm.fromIps([
    "192.168.1.65",
    "192.168.1.62",
])

stream_started = False

speed_multiplier = 60

def receive_messages():
    while True:
        data, addr = server_socket.recvfrom(1024)
        message = data.decode('utf-8')
        print(f"[RECV] From {addr}: {message}")
        global client_address
        client_address = addr
        if message == "connect":
            print(f"Client connected!")
        if len(communication.connected_tellos) > 0:
            comp = message.split("|")
            if len(comp) == 2:
                cur_ip = comp[0]
                cur_command = comp[1]
                process_command(cur_ip, cur_command)
            if len(comp) == 3:
                cur_ip = comp[0]
                cur_vel_message = comp[2]
                split_vel = cur_vel_message.split(",")
                cur_vel = (float(split_vel[0]), float(split_vel[1]), float(split_vel[2]), float(split_vel[3])) 
                process_velocity_control(cur_ip, cur_vel)
            

def send_server_messages():
    while True:
        if len(communication.message_queue) > 0 and client_address:
            message = communication.message_queue.pop()
            server_socket.sendto(message.encode('utf-8'), client_address)
            print(f"[SEND] To {HOST}: {message}")
        

def update_status_messages():
    while True:
        if len(communication.connected_tellos) > 0 and client_address:
            for tello in communication.connected_tellos:
                a = {"ip":tello.address[0], "isFlying":tello.is_flying,"battery":tello.get_battery(), "height":tello.get_height()}
                message = "Status|" + json.dumps(a)
                communication.message_queue.append(message)
        time.sleep(2)
                        

def process_command(ip : str, command:str):
    starting_swarm.parallel(lambda i, tello: parallel_command(i, tello, ip, command))

def parallel_command(i: int, tello: Tello, ip: str, cur_command: str): 
    if tello.address[0] == ip:
        match cur_command:
            case "takeoff":
                tello.takeoff()
            case "land":
                tello.land()

def process_velocity_control(ip: str, velocity: tuple[float, float, float, float]):
    starting_swarm.parallel(lambda i, tello: parallel_velocity_control(i, tello, ip, velocity))
            
            
def parallel_velocity_control(i: int, tello: Tello, ip: str, cur_velo: tuple[float, float, float, float]):
    if tello.address[0] == ip and tello.is_flying:
        tello.yaw_velocity = int(cur_velo[0] * speed_multiplier)
        tello.up_down_velocity = int(cur_velo[1] * speed_multiplier)
        tello.left_right_velocity = int(cur_velo[2] * speed_multiplier)
        tello.forward_backward_velocity = int(cur_velo[3] * speed_multiplier)
        # tello.send_rc_control(left_right_velocity, for_back_velocity, up_down_velocity, yaw_velocity)


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