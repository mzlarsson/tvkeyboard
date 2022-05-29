import json
from typing import List, Optional
from time import sleep
from custom_types import KeyBind, KeyboardLocation, KeyboardMessage, Mode
from led import setup_led_pin, set_led_pin_state, set_leds_enabled, is_leds_enabled

class Model:

    def __init__(self, send_message):
        self._send_message = send_message
        self._current_mode = 0
        self._modes = self._load_configuration()
        self._current_x = 0
        self._current_y = 0
        if self._modes[self._current_mode].on_led > 0:
            set_led_pin_state(self._modes[self._current_mode].on_led, True)
        for mode in self._modes[1:]:
            if mode.off_led > 0:
                set_led_pin_state(mode.off_led, True)

    def _load_configuration(self) -> List[Mode]:
        with open("res/modes.yaml", "r") as conf_file:
            data = json.load(conf_file)

        global_preredirects = data["global"].get("preredirects", {})
        global_redirects = data["global"].get("redirects", {})
        global_inhibits = data["global"].get("inhibit", [])

        result = []
        for mode in data["modes"]:
            keybinds = {keybind["key"]: KeyBind(**keybind) for keybind in mode["keybinds"]}
            preredirects = global_preredirects | mode.get("preredirects", {})
            redirects = global_redirects | mode.get("redirects", {})
            inhibits = global_inhibits + mode.get("inhibits", [])
            pages = [KeyboardLocation(**location) for location in mode.get("pages", [])]
            mode = Mode(mode["name"], keybinds, preredirects, redirects, inhibits, pages, mode["on_led"], mode["off_led"])
            result.append(mode)
            
            if mode.on_led > 0:
                setup_led_pin(mode.on_led)
            if mode.off_led > 0:
                setup_led_pin(mode.off_led)

        return result

    def _next_mode(self) -> None:
        # No more LED on old mode
        if self._modes[self._current_mode].on_led > 0:
            set_led_pin_state(self._modes[self._current_mode].on_led, False)
        if self._modes[self._current_mode].off_led > 0:
            set_led_pin_state(self._modes[self._current_mode].off_led, True)
        # Update index
        self._current_mode = (self._current_mode + 1) % len(self._modes)
        # Light LED for new mode
        if self._modes[self._current_mode].on_led > 0:
            set_led_pin_state(self._modes[self._current_mode].on_led, True)
        if self._modes[self._current_mode].off_led > 0:
            set_led_pin_state(self._modes[self._current_mode].off_led, False)
        print(f"Entered mode {self._modes[self._current_mode].name}")

    def _toggle_leds_enabled(self) -> None:
        print("Toggle LED visibility")
        set_leds_enabled(not is_leds_enabled())

    def _get_keybind(self, key: str) -> Optional[KeyBind]:
        return self._modes[self._current_mode].keybinds.get(key)

    def _get_page_button(self, page_no: int) -> Optional[KeyboardLocation]:
        if page_no >= 0 and page_no < len(self._modes[self._current_mode].pages):
            return self._modes[self._current_mode].pages[page_no]

    def _not_inhibited(self, key: str) -> bool:
        return key not in self._modes[self._current_mode].inhibits

    def _get_redirect(self, key: str) -> str:
        return self._modes[self._current_mode].redirects.get(key, key)

    def _get_preredirect(self, key: str) -> str:
        return self._modes[self._current_mode].preredirects.get(key, key)

    def _move_to(self, x: int, y: int, enter_on_arrival: bool) -> None:
        if self._current_x == x and self._current_y == y and enter_on_arrival:
            # Special case: We are already there. Just press enter.
            self._send_message(KeyboardMessage(0x00, ["enter"]))
            sleep(0.02)
            self._send_message(KeyboardMessage(0x00, []))
            return

        while self._current_x != x or self._current_y != y:
            # Prepare message
            msg = KeyboardMessage(0x00, [])
            if self._current_y != y:
                msg.keys.append("down" if self._current_y < y else "up")
                self._current_y += 1 if self._current_y < y else -1
            if self._current_x != x:
                msg.keys.append("right" if self._current_x < x else "left")
                self._current_x += 1 if self._current_x < x else -1
            
            if self._current_x == x and self._current_y == y and enter_on_arrival:
                msg.keys.append("enter")
            # Send message
            self._send_message(msg)
            # Wait short while
            sleep(0.02)
            # Release keys
            self._send_message(KeyboardMessage(0x00, []))
            # Wait for release to go through
            sleep(0.02)

    def _handle_keybind(self, keybind: KeyBind) -> None:
        page_btn = self._get_page_button(keybind.page)
        if page_btn:
            self._move_to(page_btn.x, page_btn.y, True)
        self._move_to(keybind.x, keybind.y, True)
        self._move_to(0, 0, False)

    def handle_key_change(self, msg: KeyboardMessage) -> None:
        if msg.has_ctrl() and len(msg.keys) == 1 and msg.keys[0] == "m":
            # Ctrl + M iterates through modes
            self._next_mode()
            return
        elif msg.has_ctrl() and len(msg.keys) == 1 and msg.keys[0] == "p":
            self._toggle_leds_enabled()

        msg.keys = list(map(self._get_preredirect, msg.keys))
        if len(msg.keys) == 1:
            # Some key is pressed
            keybind = self._get_keybind(msg.keys[0])
            if keybind:
                # Handle keybind
                self._handle_keybind(keybind)
                return
            
        # Check for inhibits and redirects
        msg.keys = list(map(self._get_redirect, filter(self._not_inhibited, msg.keys)))
        self._send_message(msg)
        