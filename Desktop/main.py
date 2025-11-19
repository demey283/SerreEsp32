import serial
import json

ser = serial.Serial("COM3", 115200) 

while True:
    line = ser.readline().decode().strip()
    try:
        data = json.loads(line)
        print("Ontvangen:", data)
    except:
        pass