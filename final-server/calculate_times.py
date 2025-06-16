import csv
from api_interface import TestsAPI
import json
from datetime import datetime
# read the CSV file and calculate the average time

TEST_ID = "test0003"
HOUSE_ID = "house01"

test_data = TestsAPI.get_tests(test_id=TEST_ID, house_id=HOUSE_ID)

fps = json.loads(test_data[0]["notes"])["fps"]
division_factor = int(90000 / fps)  # 90000 is the clock rate for RTP

measurements = test_data[0]["measurements"]

client_send_times = []
server_arrival_times = []
server_start_process_times = []
server_end_process_times = []
server_send_times = []
client_arrival_times = []

for measurement in measurements:
    if "point_a" in measurement["point"]:
        client_send_times.append((json.loads(measurement["point"])["point_a"], datetime.fromisoformat(measurement["timestamp"])))  # Convert to milliseconds
    elif "point_b" in measurement["point"]:
        server_arrival_times.append(((json.loads(measurement["point"])["point_b"] + 2) // division_factor, datetime.fromisoformat(measurement["timestamp"])))  # Convert to milliseconds
    elif "point_c" in measurement["point"]:
        server_start_process_times.append(((json.loads(measurement["point"])["point_c"] + 2) // division_factor, datetime.fromisoformat(measurement["timestamp"])))  # Convert to milliseconds
    elif "point_d" in measurement["point"]:
        server_end_process_times.append(((json.loads(measurement["point"])["point_d"] + 2) // division_factor, datetime.fromisoformat(measurement["timestamp"])))  # Convert to milliseconds
    elif "point_e" in measurement["point"]:
        server_send_times.append(((json.loads(measurement["point"])["point_e"] + 2) // division_factor, datetime.fromisoformat(measurement["timestamp"])))  # Convert to milliseconds
    elif "point_f" in measurement["point"]:
        client_arrival_times.append((json.loads(measurement["point"])["point_f"], datetime.fromisoformat(measurement["timestamp"])))  # Convert to milliseconds

server_arrival_times = iter(server_arrival_times)
server_start_process_times = iter(server_start_process_times)
server_end_process_times = iter(server_end_process_times)
server_send_times = iter(server_send_times)
client_arrival_times = iter(client_arrival_times)

with open("times.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Latency", "Frame send time", "Mediapipe Pose processing time", "Results send time"])
    
    for client_send_time in client_send_times:
        current_frame = client_send_time[0]
        server_arrival_time = next(server_arrival_times)
        while server_arrival_time[0] < current_frame:
            server_arrival_time = next(server_arrival_times)
        server_start_process_time = next(server_start_process_times)
        while server_start_process_time[0] < current_frame:
            server_start_process_time = next(server_start_process_times)

        server_end_process_time = next(server_end_process_times)
        while server_end_process_time[0] < current_frame:
            server_end_process_time = next(server_end_process_times)

        server_send_time = next(server_send_times)
        while server_send_time[0] < current_frame:
            server_send_time = next(server_send_times)

        client_arrival_time = next(client_arrival_times)
        while client_arrival_time[0] < current_frame:
            client_arrival_time = next(client_arrival_times)

        writer.writerow([
            (client_arrival_time[1] - client_send_time[1]).total_seconds() * 1000,
            (server_arrival_time[1] - client_send_time[1]).total_seconds() * 1000,
            (server_end_process_time[1] - server_start_process_time[1]).total_seconds() * 1000,
            (client_arrival_time[1] - server_send_time[1]).total_seconds() * 1000
        ])

import matplotlib.pyplot as plt
import numpy as np

# draw a graph with 4 lines, one for each row in the csv file

def draw_graph(file_path):
    data = np.genfromtxt(file_path, delimiter=',', skip_header=1)
    x = np.arange(len(data))

    plt.plot(x, data[:, 0], label='Latency')
    plt.plot(x, data[:, 1], label='Frame send time')
    plt.plot(x, data[:, 2], label='Mediapipe Pose processing time')
    plt.plot(x, data[:, 3], label='Results send time')

    plt.xlabel('Frame Number')
    plt.ylabel('Time (seconds)')
    plt.title('Latency and Processing Times')
    plt.legend()
    plt.grid()
    plt.savefig('times_graph.png')
    #plt.show()

draw_graph("times.csv")
