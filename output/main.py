import argparse
import signal
from typing import List
from serial import Serial
from custom_types import KeyboardMessage
from hid_util import hid_codes
from model import Model
from led import cleanup_gpio

logging = True
last_written_package = None

def read_packet(conn: Serial) -> KeyboardMessage:
    pkt_len = int(conn.read(1)[0])
    pkt_data = conn.read(pkt_len)
    ctrl_buttons = pkt_data[0]
    keys = []
    index = 1 # skip ctrl_button byte
    tmp = ""
    while index < pkt_len:
        while index < pkt_len and pkt_data[index] != 0x00:
            tmp += chr(pkt_data[index])
            index += 1
        keys.append(tmp)
        tmp = ""
        index += 1 # skip fill byte
    return KeyboardMessage(ctrl_buttons, keys)

def send_packet(packet: KeyboardMessage) -> None:
    hid_data = [packet.control_keys, 0x00]
    for i in range(6):
        hid_code = hid_codes.get(packet.keys[i], 0x00) if i < len(packet.keys) else 0x00
        hid_data.append(hid_code)
    hid_packet = bytes(hid_data)

    global last_written_package
    if last_written_package != hid_packet:    
        if logging:
            print(f"Sending packet: {packet}")
        try:
            with open("/dev/hidg0", "wb") as kb_out:
                kb_out.write(hid_packet)
                last_written_package = hid_packet
        except Exception as e:
            print(f"Failed to send to device: {e}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Fake keyoard!")
    parser.add_argument("--no-logging", action="store_true", help="Disable info logs (warnings will still appear)")
    parser.add_argument("--device", type=str, default="/dev/serial0", help="Serial device to talk to. Default /dev/serial0")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, cleanup_gpio)
    signal.signal(signal.SIGTERM, cleanup_gpio)

    global logging
    if args.no_logging:
        logging = False

    model = Model(send_packet)
    ser = Serial(args.device, 9600)  #Open port with baud rate
    ser.write("\n".encode("utf-8"))
    last_packet = None
    print("Ready for data!")
    try:
        while True:
            packet = read_packet(ser)
            if packet != last_packet:
                model.handle_key_change(packet)
                last_packet = packet
    except:
        pass
    cleanup_gpio()
    print("Bye!")


if __name__ == "__main__":
    main()
