import time
from machine import Pin
import onewire, ds18x20
import json
data_pin = Pin(18)  

ow = onewire.OneWire(data_pin)
ds = ds18x20.DS18X20(ow)


roms = ds.scan()
print("Gevonden sensoren:", roms)
print("test")
while True:
    ds.convert_temp()      
    time.sleep_ms(750)      
    for rom in roms:
        temp = ds.read_temp(rom)
        data ={"Temperatuur": temp}
        print(json.dumps(data))
    time.sleep(1)
