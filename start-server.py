import threading
# import queue
from djitellopy import TelloSwarm, communication, Tello
import time
import json
import socket
import keyboard
import datetime
# from NatNetClient import NatNetClient
import sys

HOST = '127.0.0.1'
PORT = 9999
CLIENT_PORT = 9998
# CLIENT_NATNET_PORT = 9997

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# natnet_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_address = None

# last_natnet_timestamp_for_ids = []


starting_swarm = TelloSwarm.fromIps([
    "192.168.1.62",
    "192.168.1.64",
])

stream_started = False

speed_multiplier = 60

def receive_messages():
    global client_address
    while True:
        try:
            data, addr = server_socket.recvfrom(1024)
            if not data:
                client_address = None
                continue
            message = data.decode('utf-8')
            print(f"[RECV] From {addr}: {message}")
            client_address = addr
            # natnet_socket.connect((client_address[0], CLIENT_NATNET_PORT))
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
        except:
            print("error receiving data")
            client_address = None
            

def send_server_messages():
    while True:
        if len(communication.message_queue) > 0 and client_address:
            message = communication.message_queue.pop()
            server_socket.sendto(message.encode('utf-8'), (client_address[0], CLIENT_PORT))
            print(f"[SEND] To {client_address}: {message}")
        

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


# def receiveRigidBody( id,pos,rot ):
#     if client_address is not None:
#         global last_natnet_timestamp_for_ids
#         for a in last_natnet_timestamp_for_ids:
#             if a[0] == id:
#                 last_natnet_timestamp = a[1]
#                 if time.time() - last_natnet_timestamp > 0.01:
#                     b = list(a)
#                     b[1] = time.time()
#                     a = tuple(b)
#                     send_rb_data(id, pos, rot)
#                 return
#         last_natnet_timestamp_for_ids.append((id, time.time()))
#         send_rb_data(id, pos, rot)

# def receiveRigidBodyList( rigidBodyList, stamp ):
#     if client_address is not None:
#         for (ac_id, pos, quat, valid) in rigidBodyList:
#             if not valid:
#                 continue
# 
#             id = str(ac_id)
# 
#             global last_natnet_timestamp_for_ids
#             id_matched = False
#             for a in last_natnet_timestamp_for_ids:
#                 if a[0] == id:
#                     id_matched = True
#                     last_natnet_timestamp = a[1]
#                     if stamp - last_natnet_timestamp > 0.02:
#                         b = list(a)
#                         b[1] = time.time()
#                         a = tuple(b)
#                         send_rb_data(id, pos, quat)
#                     break
#             if not id_matched:
#                 last_natnet_timestamp_for_ids.append((id, stamp))
#                 send_rb_data(id, pos, quat)
 

# def send_rb_data(id, pos, rot):
#     #position data
#     x = str(pos[0])
#     y = str(pos[1])
#     z = str(pos[2])
#     #quaternions
#     qx = str(rot[0])
#     qy = str(rot[1])
#     qz = str(rot[2])
#     qw = str(rot[3])
#     #build and send msg
# 
#     data_object = {"id": id, "pos": {"x": x, "y": y, "z": z}, "rot": {"x": qx, "y": qy, "z": qz, "w": qw}, "timestamp": datetime.datetime.now().strftime('%H:%M:%S:%f')}
#     msg = "natnet|" + json.dumps(data_object)
#     natnet_socket.send(bytes(msg, "utf-8"))
#     msg = "data 0 1 3 0"
#     print(str(id)+ " " + x + " "+y+" "+ z)
                

def initialize_server():
    server_socket.bind(("", PORT))
    print(f"UDP Server running on {HOST}:{PORT}")


initialize_server()


recv_thread = threading.Thread(target=receive_messages, daemon=True)
recv_thread.start()

# natnet = NatNetClient(server="192.168.1.240", local="192.168.1.196", rigidBodyListener=receiveRigidBody)
# natnet.run('d')

starting_swarm.connect()
# Start threads

send_thread = threading.Thread(target=send_server_messages, daemon=True)
update_status_thread = threading.Thread(target=update_status_messages, daemon=True)

send_thread.start()
update_status_thread.start()

# Keep the main thread alive

while True:
    if keyboard.is_pressed('p'):
        print('emergency landing!')
        starting_swarm.land()
    pass