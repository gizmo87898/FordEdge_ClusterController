import time
import can
import random
import socket
import struct
import select 
import threading
import tkinter as tk
from datetime import datetime
import win_precise_time as wpt

simulated = False

rpm = 2000
speed = 0
coolant_temp = 120
oil_temp = 120
oil_press = 2.5
boost = 10

left_directional = False
right_directional = False
tc = False
abs = False
battery = False
handbrake = False
highbeam = False
auto_highbeam = False
park_light = False

tpms = False #tbd
cruise_control = False # tbd
cruise_control_speed = 80 # tbd
foglight = False
rear_foglight = False
parking_lights = False 
check_engine = False
hood = False
trunk = False
front_left = 30
front_right = 30
rear_left = 30
rear_right = 30
airbag = False
seatbelt = False

if not simulated:
    bus = can.interface.Bus(channel='com11', bustype='seeedstudio', bitrate=500000)
    
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 4444))

# Initialize variables
id_counter = 0x1b4

start_time_100ms = time.time()
start_time_20ms = time.time()
start_time_5s = time.time()

leftpad_left = False
leftpad_right = False
leftpad_down = False
leftpad_up = False
leftpad_ok = False

# Function to toggle variable values
def toggle_var(var):
    globals()[var] = not globals()[var]

# GUI setup
def gui_thread():
    root = tk.Tk()
    root.title("Ford Edge 2011")

    
    leftpad_up = tk.Button(root, text=f"L UP")
    leftpad_up.grid(row=0, column=1)
    leftpad_up.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_up"))
    leftpad_up.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_up"))

    leftpad_down = tk.Button(root, text=f"L DOWN")
    leftpad_down.grid(row=2, column=1)
    leftpad_down.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_down"))
    leftpad_down.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_down"))
    
    leftpad_left = tk.Button(root, text=f"L LEFT")
    leftpad_left.grid(row=1, column=0)
    leftpad_left.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_left"))
    leftpad_left.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_left"))
    
    leftpad_right = tk.Button(root, text=f"L RIGHT")
    leftpad_right.grid(row=1, column=2)
    leftpad_right.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_right"))
    leftpad_right.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_right"))
    
    leftpad_ok = tk.Button(root, text=f"L OK")
    leftpad_ok.grid(row=1, column=1)
    leftpad_ok.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_ok"))
    leftpad_ok.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_ok"))
    
    rightpad_up = tk.Button(root, text=f"L UP")
    rightpad_up.grid(row=0, column=5)
    rightpad_up.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_up"))
    rightpad_up.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_up"))
    
    rightpad_down = tk.Button(root, text=f"L UP")
    rightpad_down.grid(row=1, column=4)
    rightpad_down.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_up"))
    rightpad_down.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_up"))
    
    rightpad_left = tk.Button(root, text=f"L UP")
    rightpad_left.grid(row=1, column=6)
    rightpad_left.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_up"))
    rightpad_left.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_up"))
    
    rightpad_right = tk.Button(root, text=f"L UP")
    rightpad_right.grid(row=2, column=5)
    rightpad_right.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_up"))
    rightpad_right.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_up"))
    
    rightpad_ok = tk.Button(root, text=f"L UP")
    rightpad_ok.grid(row=1, column=5)
    rightpad_ok.bind('<ButtonPress-1>', lambda event: toggle_var("leftpad_up"))
    rightpad_ok.bind('<ButtonRelease-1>', lambda event: toggle_var("leftpad_up"))
    
    root.mainloop()

gui_thread = threading.Thread(target=gui_thread)
gui_thread.start()

# Function to toggle lights using a for loop
def toggle_lights():
    global rpm, speed, tpms, cruise_control, foglight, parking_lights, check_engine, hood, trunk, airbag, seatbelt
    global left_directional, right_directional, tc, abs, battery, handbrake, highbeam, rear_foglight

    lights_to_toggle = [
        'rpm', 'speed', 'tpms', 'cruise_control', 'foglight', 'parking_lights',
        'check_engine', 'hood', 'trunk', 'airbag', 'seatbelt', 'left_directional',
        'right_directional', 'tc', 'abs', 'battery', 'handbrake', 'highbeam', 'rear_foglight'
    ]

    for light in lights_to_toggle:
        toggle_var(light)

# Main loop
while True:
    current_time = time.time()
    ready_to_read, _, _ = select.select([sock], [], [], 0)

    if sock in ready_to_read:
        data, _ = sock.recvfrom(256)
        packet = struct.unpack('I4sH2c7f2I3f16s16si', data)
        
        rpm = int(max(min(packet[6], 8000), 0))
        speed = max(min(int(packet[5]*2.5), 255), 0)
        left_directional = False
        right_directional = False
        highbeam = (packet[13] >> 1) & 1
        handbrake = (packet[13] >> 2) & 1
        tc = (packet[13] >> 4) & 1
        abs = (packet[13] >> 10) & 1
        battery = (packet[13] >> 9) & 1
        left_directional = (packet[13] >> 5) & 1
        right_directional = (packet[13] >> 6) & 1
            
    # Process messages at different intervals
    elapsed_time_100ms = current_time - start_time_100ms
    if elapsed_time_100ms >= 0.5:
        date = datetime.now()
        messages_100ms = [
            can.Message(arbitration_id=0x3b3, data=[0x40, 0x48, 0x02, 0x0f, 0x10, 0x05, 0x00, 0x22], is_extended_id=False),
            can.Message(arbitration_id=id_counter, data=[random.randint(0, 255) for _ in range(8)], is_extended_id=False),
        ]

        for message in messages_100ms:
            if not simulated:
                bus.send(message)
            else:
                print(message)
        start_time_100ms = time.time()

    elapsed_time_20ms = current_time - start_time_20ms
    if elapsed_time_20ms >= 0.02:
        messages_20ms = [
            can.Message(arbitration_id=0x3a3, data=[0, 0, int(rpm/3) & 0xff, int(rpm/3) >> 8, 0, 0, 0, 0], is_extended_id=False),
            can.Message(arbitration_id=0x81, data=[(leftpad_down * 1) +(leftpad_ok * 16) +(leftpad_left * 2) + (leftpad_right * 4) + (leftpad_up * 8), 0, 0, 0, 0, 0, 0, 0], is_extended_id=False),
        ]
        
        for message in messages_20ms:
            if not simulated:
                bus.send(message)
            else:
                print(message)
        start_time_20ms = time.time()

    elapsed_time_5s = current_time - start_time_5s
    if elapsed_time_5s >= 3:
        toggle_lights()
        id_counter += 1
        print(hex(id_counter))
        start_time_5s = time.time()

# Close the socket
sock.close()
