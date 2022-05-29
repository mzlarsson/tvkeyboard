
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

class ControlKeyName(Enum):
    LEFT_CTRL = 0
    LEFT_SHIFT = 1
    LEFT_ALT = 2
    LEFT_META = 3
    RIGHT_CTRL = 4
    RIGHT_SHIFT = 5
    RIGHT_ALT = 6
    RIGHT_META = 7


@dataclass
class KeyboardMessage:
    control_keys: int
    keys: List[str]

    def get_control_key_bit(self, key: ControlKeyName) -> bool:
        bit = key.value
        return (self.control_keys & (0x01 << bit)) > 0

    def set_control_key_bit(self, key: ControlKeyName, on: bool) -> None:
        bit = key.value
        self.control_keys &= ~(0x01 << bit)
        self.control_keys |= (on << bit)

    def has_shift(self) -> bool:
        return (self.get_control_key_bit(ControlKeyName.LEFT_SHIFT) or
                self.get_control_key_bit(ControlKeyName.RIGHT_SHIFT))

    def has_ctrl(self) -> bool:
        return (self.get_control_key_bit(ControlKeyName.LEFT_CTRL) or
                self.get_control_key_bit(ControlKeyName.RIGHT_CTRL))

    def has_alt(self) -> bool:
        return (self.get_control_key_bit(ControlKeyName.LEFT_ALT) or
                self.get_control_key_bit(ControlKeyName.RIGHT_ALT))

@dataclass
class KeyboardLocation:
    x: int
    y: int

@dataclass
class KeyBind:
    key: str
    x: int
    y: int
    page: int = -1

@dataclass
class Mode:
    name: str
    keybinds: Dict[str, KeyBind]
    preredirects: Dict[str, str]
    redirects: Dict[str, str]
    inhibits: List[str]
    pages: Optional[List[KeyboardLocation]]
    start: Tuple[int, int]
    on_led: int = -1
    off_led: int = -1