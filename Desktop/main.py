import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import json
import time
import csv
from collections import deque

# Seriële instellingen
SERIAL_PORT = "COM3"
BAUDRATE = 115200
CSV_FILE = "temperatuur_data.csv"
MAX_POINTS = None  # Geen limiet op het aantal punten

# Parent class voor temperatuur monitoring
class TemperatureMonitor:
    def __init__(self, serial_port, baudrate, max_points=None):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.ser = None
        # deque is een datastructuur waarmee je gemakkelijk data van achter en voor kan toevoegen en verwijderen
        self.data_queue = deque(maxlen=max_points)
        self.timestamps = deque(maxlen=max_points)
        self.setup_serial()

    # Functie om verbinding te maken met de seriële poort
    def setup_serial(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=0.1)
            print(f"Verbonden met {self.serial_port}")
            time.sleep(2)

            # Tijd synchroniseren, want de ESP32 heeft geen echte klok
            sync_msg = {"type": "sync_time", "timestamp": int(time.time())}
            self.ser.write((json.dumps(sync_msg) + "\n").encode())
            print("Tijd gesynchroniseerd")
            time.sleep(0.5)

            # Start signaal om de meting te starten
            self.ser.write((json.dumps({"type": "start"}) + "\n").encode())
            print("Start-signaal verzonden")
        except Exception as e:
            print("Kan seriële poort niet openen:", e)
            self.ser = None

# Subclass die CSV-logging toevoegt
class CSVLogger(TemperatureMonitor):
    def __init__(self, serial_port, baudrate, csv_file, max_points=None):
        super().__init__(serial_port, baudrate, max_points) #roept de constructor van de parent class aan
        self.csv_file = csv_file

        # Initialiseer CSV-bestand en laad bestaande data
        try:
            with open(self.csv_file, "r") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) == 2:  # Controleer of er twee kolommen zijn
                        ts = int(row[0])
                        temp = float(row[1])
                        self.timestamps.append(ts)  # tijdstip toevoegen aan de lijst
                        self.data_queue.append(temp)  # temperatuur toevoegen aan de lijst
        except FileNotFoundError:
            with open(self.csv_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Tijd", "Temperatuur"])  # header

    # Functie om seriële regel te verwerken en op te slaan in CSV
    def process_serial_line(self, line):
        try:
            data = json.loads(line)  # Laad JSON data
            if "Temperatuur" in data and "Tijd" in data:
                temp = float(data["Temperatuur"])
                ts = int(data["Tijd"])
                self.data_queue.append(temp)
                self.timestamps.append(ts)

                # Sla de data op in CSV
                with open(self.csv_file, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([ts, temp])
        except:
            pass  # Als iets misgaat bij JSON parsing, gewoon negeren

# Setup plot
fig, ax = plt.subplots()
line, = ax.plot([], [], linewidth=2, color='red')
ax.set_xlabel("Tijd")
ax.set_ylabel("Temperatuur (°C)")
ax.set_ylim(0, 50)

# Maak object van subclass
monitor = CSVLogger(SERIAL_PORT, BAUDRATE, CSV_FILE, MAX_POINTS)

# Animatie functie die elke interval wordt opgeroepen om de plot bij te werken
def animate(i):
    if monitor.ser:
        try:
            raw = monitor.ser.readline()  # Lees een regel van de seriële poort
            if raw:
                line_data = raw.decode("utf-8").strip()  # Decodeer de data en verwijder witruimte
                if line_data.startswith("{"):  # Controleer of het een JSON-bericht is
                    monitor.process_serial_line(line_data)  # Verwerk de data
        except Exception as e:
            print("Fout bij lezen:", e)

    if monitor.data_queue:  # Wanneer er iets binnen is gekomen wordt de plot bijgewerkt
        xs = list(monitor.timestamps)
        ys = list(monitor.data_queue)
        line.set_data(xs, ys)
        ax.set_xlim(min(xs), max(xs))
        ax.set_ylim(min(ys)-2, max(ys)+2)  # Past de limieten aan

        # Stap zodat de x-as niet te vol wordt
        step = max(1, len(xs)//10)
        ax.set_xticks(xs[::step])
        ax.set_xticklabels(
            [time.strftime("%H:%M:%S", time.localtime(t)) for t in xs[::step]],
            rotation=45
        )
    return line,

# Start animatie
ani = animation.FuncAnimation(
    fig,
    animate,
    interval=200,
    cache_frame_data=False
)

plt.tight_layout()  # Zorgt ervoor dat alles netjes in beeld komt
plt.show()
