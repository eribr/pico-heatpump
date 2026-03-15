# IR Driver for Nibe Heat Pump

import time

# MicroPython-specific imports
try:
    from machine import Pin
    MICROPYTHON = True
except ImportError:
    MICROPYTHON = False

class IRDriver:
    def __init__(self, pin_number):
        if not MICROPYTHON:
            self.ir_pin = None
            self.pin_number = pin_number
        else:
            self.ir_pin = Pin(pin_number, Pin.OUT)
        self.frequency = 38  # Default frequency in kHz

    def set_frequency(self, frequency):
        if not MICROPYTHON:
            print(f"IR Driver: Simulating frequency set to {frequency}kHz")
        self.frequency = frequency

    def mark(self, duration):
        if not MICROPYTHON:
            print(f"IR Driver: Simulating mark for {duration}us")
            time.sleep_us(duration) if hasattr(time, 'sleep_us') else time.sleep(duration / 1000000)
            return
        self.ir_pin.on()
        time.sleep_us(duration)
        self.ir_pin.off()

    def space(self, duration):
        if not MICROPYTHON:
            print(f"IR Driver: Simulating space for {duration}us")
            time.sleep_us(duration) if hasattr(time, 'sleep_us') else time.sleep(duration / 1000000)
            return
        self.ir_pin.off()
        time.sleep_us(duration)

    def send_ir_byte(self, byte, bit_mark, zero_space, one_space):
        for i in range(8):
            if byte & (1 << (7 - i)):
                self.mark(bit_mark)
                self.space(one_space)
            else:
                self.mark(bit_mark)
                self.space(zero_space)

    def send_ir_message(self, message):
        self.set_frequency(38)  # Set frequency to 38 kHz
        self.mark(9000)  # Header mark
        self.space(4500)  # Header space

        for byte in message:
            self.send_ir_byte(byte, 560, 560, 1690)  # Send each byte

        self.mark(560)  # End mark
        self.space(0)  # End space

    # Alias for the legacy API used by NibeHeatpumpIR
    def send_ir(self, message):
        self.send_ir_message(message)
