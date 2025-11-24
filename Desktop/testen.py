import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
from collections import deque
import json

SERIAL_PORT = "COM3"
BAUDRATE = 115200
MAX_POINTS = 300

data_queue = deque(maxlen=MAX_POINTS)

try:
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    print(f"Verbonden met {SERIAL_PORT}")
except Exception as e:
    print("Kan seriële poort niet openen:", e)
    ser = None

fig, ax = plt.subplots()
line, = ax.plot([], [])
ax.set_xlabel("Samples")
ax.set_ylabel("Temperatuur (°C)")
ax.set_ylim(0, 50)

def animate(i):
    if ser:
        try:
            line_data = ser.readline().decode('utf-8', errors='ignore').strip()
            if line_data:
                data_json = json.loads(line_data)
                temp = float(data_json.get("Temperatuur"))
                data_queue.append(temp)
        except:
            pass
    if data_queue:
        xs = list(range(len(data_queue)))
        ys = list(data_queue)
        line.set_data(xs, ys)
        ax.set_xlim(max(0, len(xs)-MAX_POINTS), max(MAX_POINTS, len(xs)))
        ax.set_ylim(min(ys)-2, max(ys)+2)
    return line,

ani = animation.FuncAnimation(fig, animate, interval=100)
plt.show()
