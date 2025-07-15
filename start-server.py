import threading
# import queue
from djitellopy import TelloSwarm, communication, Tello
import time
import json
import socket
import keyboard

HOST = '127.0.0.1'
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_address = None

starting_swarm = TelloSwarm.fromIps([
    "192.168.1.64",
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
            if len(comp) > 1:
                match comp[0]:
                    case "drone_command":
                        pass 
                    case "drone_velocity_command":
                        pass 
                    case "swarm_command":
                        process_swarm_command(comp[1:])
                    case "swarm_velocity_command":
                        # not used: velocity command processed locally in Unity
                        process_swarm_velocity_command(comp[1:])
            

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
                        

def process_swarm_command(commands: list):
    starting_swarm.parallel(lambda i, tello: parallel_command(i, tello, commands))

def parallel_command(i: int, tello: Tello, commands: list):
    for command in commands:
        loaded_command = json.loads(command)
        if loaded_command["ip"] == tello.address[0]:
            match loaded_command["command"]:
                case "takeoff":
                    tello.takeoff()
                case "land":
                    tello.land()

# not used: velocity command processed locally in Unity
def process_swarm_velocity_command(commands: list):
    starting_swarm.parallel(lambda i, tello: parallel_velocity_control(i, tello, commands))
            
# not used: velocity command processed locally in Unity          
def parallel_velocity_control(i: int, tello: Tello, commands: list):
    for command in commands:
        loaded_command = json.loads(command)
        if loaded_command["ip"] == tello.address[0]:
            tello.yaw_velocity = int(float(loaded_command["input"]["x"]) * speed_multiplier)
            tello.up_down_velocity = int(float(loaded_command["input"]["y"]) * speed_multiplier)
            tello.left_right_velocity = int(float(loaded_command["input"]["z"])  * speed_multiplier)
            tello.forward_backward_velocity = int(float(loaded_command["input"]["w"])  * speed_multiplier)
            tello.rc_control_updating = True


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
    if keyboard.is_pressed('p'):
        print('emergency landing!')
        starting_swarm.land()
    pass