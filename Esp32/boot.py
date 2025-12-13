import time
from machine import Pin
import onewire, ds18x20
import json

data_pin = Pin(18)
ow = onewire.OneWire(data_pin)
ds = ds18x20.DS18X20(ow)
roms = ds.scan()
filename = "data.json"

try:
    with open(filename, "r") as f:
        pass
except:
    with open(filename, "w") as f:
        json.dump([], f)

while True:
    ds.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
        temp = ds.read_temp(rom)
        entry = {"Temperatuur": temp, "Tijd": time.time()}

        with open(filename, "r") as f:
            data = json.load(f)
        data.append(entry)
        with open(filename, "w") as f:
            json.dump(data, f)

        for e in data:
            local_time = time.localtime(e["Tijd"])
            print("{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} Temp: {:.2f}°C".format(
                local_time[0], local_time[1], local_time[2],
                local_time[3], local_time[4], local_time[5],
                e["Temperatuur"]
            ))

    time.sleep(5)
