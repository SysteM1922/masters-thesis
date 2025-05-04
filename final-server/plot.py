from matplotlib import pyplot as plt

times = []

with open("times.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    time = float(line.strip())
    times.append(time)

# times should be on y axis and the index of the list should be on x axis
plt.plot(times, linestyle='-', color='b')
plt.title("Latency over time")
plt.xlabel("Frame Number")
plt.ylabel("Latency (seconds)")
plt.grid()

plt.savefig("times.png")
plt.show()
