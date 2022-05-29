import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

pin_states = {}
pins_enabled = True

def setup_led_pin(pin_no: int) -> None:
    GPIO.setup(pin_no, GPIO.OUT)
    set_led_pin_state(pin_no, False)

def set_led_pin_state(pin_no: int, on: bool) -> None:
    pin_states[pin_no] = 1 if on else 0
    if pins_enabled:
        _set_pin_output(pin_no, pin_states[pin_no])

def set_leds_enabled(enabled: bool) -> None:
    global pins_enabled
    if pins_enabled == enabled:
        # No change
        return

    pins_enabled = enabled
    for pin_no in pin_states:
        _set_pin_output(pin_no, 0 if not pins_enabled else pin_states[pin_no])

def is_leds_enabled() -> bool:
    return pins_enabled

def _set_pin_output(pin_no: int, output: int) -> None:
    GPIO.output(pin_no, output)

def cleanup_gpio() -> None:
    GPIO.cleanup()