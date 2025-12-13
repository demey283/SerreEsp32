import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import json
import time
import csv
from collections import deque

SERIAL_PORT = "COM3"
BAUDRATE = 115200

MAX_POINTS = None
data_queue = deque(maxlen=MAX_POINTS)
timestamps = deque(maxlen=MAX_POINTS)

CSV_FILE = "temperatuur_data.csv"
try:
    with open(CSV_FILE, "r") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) == 2:
                ts = int(row[0])
                temp = float(row[1])
                timestamps.append(ts)
                data_queue.append(temp)
except FileNotFoundError:
    with open(CSV_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Tijd", "Temperatuur"])  # header

try:
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    print(f"Verbonden met {SERIAL_PORT}")
except Exception as e:
    print("Kan seriële poort niet openen:", e)
    ser = None

time.sleep(2)

if ser:
    sync_msg = {"type": "sync_time", "timestamp": int(time.time())}
    ser.write((json.dumps(sync_msg) + "\n").encode())
    print("Tijd gesynchroniseerd")

    time.sleep(0.5)

    ser.write((json.dumps({"type": "start"}) + "\n").encode())
    print("Start-signaal verzonden")

fig, ax = plt.subplots()
line, = ax.plot([], [], linewidth=2)
ax.set_xlabel("Tijd")
ax.set_ylabel("Temperatuur (°C)")
ax.set_ylim(0, 50)

def animate(i):
    if ser:
        try:
            raw = ser.readline()
            if not raw:
                return line,
            line_data = raw.decode("utf-8").strip()
            if not line_data.startswith("{"):
                return line
            data = json.loads(line_data)

            if "Temperatuur" in data and "Tijd" in data:
                temp = float(data["Temperatuur"])
                ts = int(data["Tijd"])
                data_queue.append(temp)
                timestamps.append(ts)


                with open(CSV_FILE, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([ts, temp])
        except Exception as e:
            print("Fout bij lezen:", e)

    if data_queue:
        xs = list(timestamps)
        ys = list(data_queue)
        line.set_data(xs, ys)
        ax.set_xlim(min(xs), max(xs))
        ax.set_ylim(min(ys)-2, max(ys)+2)

        step = max(1, len(xs)//10)
        ax.set_xticks(xs[::step])
        ax.set_xticklabels([time.strftime("%H:%M:%S", time.localtime(t)) for t in xs[::step]], rotation=45)

    return line,

ani = animation.FuncAnimation(
    fig,
    animate,
    interval=200,
    cache_frame_data=False
)

plt.tight_layout()
plt.show()
