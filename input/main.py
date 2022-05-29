#!/usr/bin/python

import keyboard
from dataclasses import dataclass
import serial
import json
import argparse

@dataclass
class ControlKeys:
    left_ctrl: bool
    left_shift: bool
    left_alt: bool
    left_meta: bool
    right_ctrl: bool
    right_shift: bool
    right_alt: bool
    right_meta: bool

    def get_state(self):
        return self.left_ctrl << 0 | self.left_shift << 1 | \
               self.left_alt << 2 | self.left_meta << 3 | \
               self.right_ctrl << 4 | self.right_shift << 5 | \
               self.right_alt << 6 | self.right_meta << 7

    def altgr_active(self):
        return self.right_alt

    def shift_active(self):
        return self.left_shift or self.right_shift

serial_connection = None
control_keys = ControlKeys(False, False, False, False, False, False, False, False)
active_keys = set()
logging = True
numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] # const

def set_control_key(code, name, value):
    if code == 29:
        if " " in name:
            control_keys.right_ctrl = value
        else:
            control_keys.left_ctrl = value
    elif code == 42:
        control_keys.left_shift = value
    elif code == 56:
        control_keys.left_alt = value
    elif code == 91 or code == 125:
        control_keys.left_meta = value
    elif code == 54:
        control_keys.right_shift = value
    elif code == 100:
        control_keys.right_alt = value
    elif code == 93:
        control_keys.right_meta = value
    else:
        return False
    return True


def send():
    # Format: Length (1 byte), ControlButtons (1 byte), Char1 (n bytes), 0x00, Char2 (m bytes), ..., CharN (k bytes)
    data = [0x00, control_keys.get_state()]
    first = True
    for key in active_keys:
        chars = [ord(char) for char in key]
        if any((c > 255 for c in chars)):
            print(f"Key {key} contains invalid characters: {chars}")
            continue
        if not first:
            data.append(0x00)
        data.extend(chars)
        first = False
    data[0] = len(data) - 1 # skip length byte

    if serial_connection:
        serial_connection.write(data)
    else:
        print("Could not send update: No connection exists")

def handle_key_press(event):
    if logging:
        print(f"Pressed {event.name} {event.scan_code}")
    if not set_control_key(event.scan_code, event.name, True):
        active_keys.add(event.name)
    send()

def handle_key_release(event):
    if logging:
        print(f"Released {event.name}")
    if not set_control_key(event.scan_code, event.name, False):
        if event.name in active_keys:
            active_keys.remove(event.name)
        else:
            print("Warning: Released key which wasn't in active_keys")
    send()

def handle_key_event(event):
    original_name = event.name
    if event.scan_code == 99 and event.name == "unknown":
        event.name = "prtscn" # print screen key
    elif event.is_keypad and event.name in numbers:
        event.name = f"num{event.name}"
    elif event.scan_code == 125:
        event.name = "win_meta"
    elif event.scan_code == 164:
        event.name = "play"

    if event.event_type == "down":
        handle_key_press(event)
    elif event.event_type == "up":
        handle_key_release(event)

def main():
    parser = argparse.ArgumentParser(description="Fake keyoard!")
    parser.add_argument("--no-logging", action="store_true", help="Disable info logs (warnings will still appear)")
    parser.add_argument("--device", type=str, default="/dev/serial0", help="Serial device to talk to. Default /dev/serial0")
    args = parser.parse_args()

    global logging
    if args.no_logging:
        logging = False

    global serial_connection
    try:
        serial_connection = serial.Serial(args.device, 9600)
        keyboard.hook(handle_key_event)
        print("Ready for data!")
        keyboard.wait()
    except KeyboardInterrupt as kbe:
        print("Got KeyInterrupt, stopping...")
        serial_connection.close()
    print("Bye!")

if __name__ == "__main__":
    main()
