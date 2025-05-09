import csv

# read the CSV file and calculate the average time

client_send_times = []
server_arrival_times = []
server_start_process_times = []
server_end_process_times = []
server_send_times = []
client_arrival_times = []
frame_indexes = []

def read_csv(file_path, time_list, frame_index_list):
    if len(frame_index_list) == 0:
        with open(file_path, 'r') as csvfile:
            csvfile.readline()  # Skip the header
            reader = csv.reader(csvfile)
            for row in reader:
                frame_index_list.append(int(row[0]))
                time_list.append(float(row[-1]))
    else:
        with open(file_path, 'r') as csvfile:
            csvfile.readline()
            reader = csv.reader(csvfile)
            for row in reader:
                if int(row[0]) in frame_index_list:
                    time_list.append(float(row[-1]))

read_csv("point_f.csv", client_arrival_times, frame_indexes)
read_csv("point_e.csv", server_send_times, frame_indexes)
read_csv("point_d.csv", server_end_process_times, frame_indexes)
read_csv("point_c.csv", server_start_process_times, frame_indexes)
read_csv("point_b.csv", server_arrival_times, frame_indexes)
read_csv("point_a.csv", client_send_times, frame_indexes)

with open("times.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Latency", "Frame send time", "Mediapipe Pose processing time", "Results send time"])
    for i in range(len(frame_indexes)):
        writer.writerow([
            client_arrival_times[i] - client_send_times[i],
            server_arrival_times[i] - client_send_times[i],
            server_end_process_times[i] - server_start_process_times[i],
            client_arrival_times[i] - server_send_times[i]
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
    plt.show()

draw_graph("times.csv")
