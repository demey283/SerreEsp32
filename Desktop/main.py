import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import json
import time
import csv
from collections import deque

# insetllinge voor de seriele communicatie
SERIAL_PORT = "COM3"
BAUDRATE = 115200

MAX_POINTS = None
# deque is een data structuur waarmee je gemakkelijk data van achter en vanoor  kan toevoegen
# en verwijderen
data_queue = deque(maxlen=MAX_POINTS)
timestamps = deque(maxlen=MAX_POINTS)

CSV_FILE = "temperatuur_data.csv"
try:
    with open(CSV_FILE, "r") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) == 2: #controleert of er 2 kollomen zjin
                ts = int(row[0])
                temp = float(row[1])
                timestamps.append(ts) #tijdstip toevoegen aan de lijst
                data_queue.append(temp) #temperatuur toevoegen aan de lijst
except FileNotFoundError:
    with open(CSV_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Tijd", "Temperatuur"])  # header
# verbinding maken met de seriele poort
try:
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    print(f"Verbonden met {SERIAL_PORT}")
except Exception as e:
    print("Kan seriële poort niet openen:", e)
    ser = None

time.sleep(2) 

if ser:
    #een sync bericht om zo de tijd te synchroniseren want de esp32 heeft geen echte klok
    sync_msg = {"type": "sync_time", "timestamp": int(time.time())} 
    ser.write((json.dumps(sync_msg) + "\n").encode())
    print("Tijd gesynchroniseerd")

    time.sleep(0.5)

    #een start bericht om zo de meting te starten

    ser.write((json.dumps({"type": "start"}) + "\n").encode())
    print("Start-signaal verzonden")
# dit zet de plot op
fig, ax = plt.subplots()
line, = ax.plot([], [], linewidth=2, color='red')
ax.set_xlabel("Tijd")
ax.set_ylabel("Temperatuur (°C)")
ax.set_ylim(0, 50)
# deze functie wordt elke keer opgeropen om de plot bij te werken
def animate(i):
    if ser:
        try:
            raw = ser.readline() #leest  regel van de poort
            if not raw: 
                return line,
            line_data = raw.decode("utf-8").strip() #decodeert de data en stript witruimte
            if not line_data.startswith("{"): #controleert of het een json bericht is
                return line
            data = json.loads(line_data) #laadt de json data

            #hier wordt de data opgehaald en opgeslagen
            if "Temperatuur" in data and "Tijd" in data:
                temp = float(data["Temperatuur"]) 
                ts = int(data["Tijd"])
                data_queue.append(temp)
                timestamps.append(ts)

                #hier wordt de data opgeslagen in een csv bestand
                with open(CSV_FILE, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([ts, temp])
        except Exception as e:
            print("Fout bij lezen:", e)

    if data_queue: #wanneer er iets binnen is gekomen wordt de plot bijgewerkt
        xs = list(timestamps)
        ys = list(data_queue)
        
        line.set_data(xs, ys)
        ax.set_xlim(min(xs), max(xs))
        ax.set_ylim(min(ys)-2, max(ys)+2)#past de limieten aan 

        step = max(1, len(xs)//10)#dit zorgt voor een stap zodat de x-as niet te vol wordt
        ax.set_xticks(xs[::step]) #neem elke stap een waarde uit xs
        ax.set_xticklabels([time.strftime("%H:%M:%S", time.localtime(t)) for t in xs[::step]], rotation=45) #neemt de locale tijd en ook een omzetting

    return line,
#maak het object
ani = animation.FuncAnimation(
    fig,
    animate,
    interval=200,
    cache_frame_data=False
)

plt.tight_layout() #zorgt ervoor dat alles netjes in beeld komt
plt.show()
