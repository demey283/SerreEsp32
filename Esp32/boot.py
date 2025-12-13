import time
import json
from machine import Pin
import onewire, ds18x20
import sys
import uselect


poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)


DATA_PIN = 18
data_pin = Pin(DATA_PIN)
ow = onewire.OneWire(data_pin)
ds = ds18x20.DS18X20(ow)
roms = ds.scan()
print("DS18B20 gevonden:", roms)


time_offset = 0
started = False


print(json.dumps({"status": "ready"}))


def check_serial():
    global time_offset, started
    if poll.poll(0):
        try:
            line = sys.stdin.readline().strip()
            data = json.loads(line)
            if data.get("type") == "sync_time":
                pc_time = int(data["timestamp"])
                time_offset = pc_time - int(time.time())
                print(json.dumps({"status": "time_synced"}))
            elif data.get("type") == "start":
                started = True
                print(json.dumps({"status": "started"}))
        except:
            pass


while not started:
    check_serial()
    time.sleep(0.1)


while True:
    check_serial()

    ds.convert_temp()
    time.sleep_ms(750)

    for rom in roms:
        temp = ds.read_temp(rom)
        current_time = int(time.time() + time_offset)


        print(json.dumps({
            "Temperatuur": temp,
            "Tijd": current_time
        }))

    time.sleep(5)

