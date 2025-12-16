import time  # Voor tijdfuncties zoals time.time(), time.sleep() en time.sleep_ms()
import json  # Voor het coderen/decoderen van JSON-berichten
from machine import Pin  # Voor het werken met GPIO-pinnen op de microcontroller
import onewire, ds18x20  # Voor het uitlezen van DS18B20 temperatuursensoren
import sys  # Voor toegang tot stdin (seriële input)
import uselect  # Voor non-blocking polling van stdin

# Poll-object aanmaken om te checken of er data beschikbaar is op stdin
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)  # Registreer stdin voor polling op input

# GPIO-pin waar de DS18B20 op is aangesloten
DATA_PIN = 18
data_pin = Pin(DATA_PIN)

# OneWire object aanmaken om te communiceren met DS18B20
ow = onewire.OneWire(data_pin)
ds = ds18x20.DS18X20(ow)

# Zoek alle aangesloten DS18B20 sensoren
roms = ds.scan()
print("DS18B20 gevonden:", roms)  # Laat de gevonden sensoren zien

# Variabelen voor tijdssynchronisatie en startstatus
time_offset = 0  # Verschil tussen PC-tijd en microcontroller-tijd
started = False  # Of de meting al gestart is

# Laat weten dat het script klaar is om commando's te ontvangen
print(json.dumps({"status": "ready"}))


# Functie om seriële input te controleren en te verwerken
def check_serial():
    global time_offset, started
    if poll.poll(0):  # Check of er input beschikbaar is (non-blocking)
        try:
            line = sys.stdin.readline().strip()  # Lees een regel en verwijder spaties/newlines
            data = json.loads(line)  # Converteer JSON-string naar dictionary
            if data.get("type") == "sync_time":  # Tijd synchronisatie bericht
                pc_time = int(data["timestamp"])
                time_offset = pc_time - int(time.time())  # Bereken verschil tussen PC en microcontroller
                print(json.dumps({"status": "time_synced"}))  # Bevestiging terugsturen
            elif data.get("type") == "start":  # Start-commando ontvangen
                started = True
                print(json.dumps({"status": "started"}))  # Bevestiging terugsturen
        except:
            pass  # Als iets misgaat bij JSON parsing, gewoon negeren


# Wacht totdat het start-commando is ontvangen
while not started:
    check_serial()  # Controleer continu op seriële input
    time.sleep(0.1)  # Klein interval om CPU niet volledig te blokkeren


# Hoofdloop die continu temperaturen leest
while True:
    check_serial()  # Blijf controleren op seriële commando's

    ds.convert_temp()  # Start temperatuurmeting op alle sensoren
    time.sleep_ms(750)  # Wacht 750 ms voor de meting klaar is (DS18B20 specificatie)

    # Lees temperatuur van elke sensor
    for rom in roms:
        temp = ds.read_temp(rom)  # Lees temperatuur in °C
        current_time = int(time.time() + time_offset)  # Pas tijd aan met eventuele offset

        # Stuur temperatuur en tijd als JSON naar stdout (serieel)
        print(json.dumps({
            "Temperatuur": temp,
            "Tijd": current_time
        }))

    time.sleep(5)  # Wacht 5 seconden voor de volgende meting
