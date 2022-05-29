import serial
#Serial takes two parameters: serial device and baudrate
ser = serial.Serial('/dev/serial0', 9600)

print("Reading from serial")
while True:
    data = ser.read()
    print(data)

print("Bye")