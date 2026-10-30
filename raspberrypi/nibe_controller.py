import sys
import time
import pigpio
from nibe_protocol import generate_nibe_packet, get_current_time_gmt1


class NibeController:
    """
    Nibe IR Controller - Sends dynamically generated IR signals.
    
    Uses nibe_protocol.py to generate correct byte sequences
    based on time and settings instead of static recordings.
    """

    def __init__(self, ir_pin=17):
        self.ir_pin = ir_pin
        self.state = {
            "power": "on",
            "mode": "HEAT",
            "temp": 22,
            "fan": "AUTO",
            "ifeel": False,
        }
        self.pi = pigpio.pi()

        if not self.pi.connected:
            print(
                "Error: pigpiod is not running! Start it with 'sudo pigpiod'."
            )
            sys.exit(1)

        self.pi.set_mode(self.ir_pin, pigpio.OUTPUT)

    def _send_pulses(self, pulse_list):
        """Generate the 38kHz carrier wave and transmit pulses via pigpio."""
        self.pi.wave_clear()
        wave = []

        for i, us in enumerate(pulse_list):
            if i % 2 == 0:  # Mark (38kHz carrier wave: ~13us high, ~13us low)
                cycles = int(us / 26)
                for _ in range(cycles):
                    wave.append(pigpio.pulse(1 << self.ir_pin, 0, 13))
                    wave.append(pigpio.pulse(0, 1 << self.ir_pin, 13))
            else:  # Space
                wave.append(pigpio.pulse(0, 1 << self.ir_pin, us))

        self.pi.wave_add_generic(wave)
        wid = self.pi.wave_create()

        if wid >= 0:
            self.pi.wave_send_once(wid)
            while self.pi.wave_tx_busy():
                time.sleep(0.01)
            self.pi.wave_delete(wid)
            return True
        return False

    def _bytes_to_pulses(self, byte_packet):
        """
        Convert 11 bytes to IR pulses (microseconds).
        
        Args:
            byte_packet: List of 11 bytes
            
        Returns:
            List of pulses (mark/space pairs)
        """
        # Header: 6370us mark, 3200us space
        pulses = [6370, 3200]
        
        # For each byte, send 8 bits (LSB first)
        for byte_val in byte_packet:
            for bit_idx in range(8):
                bit = (byte_val >> bit_idx) & 1
                # Mark: ~420us
                pulses.append(420)
                # Space: ~2140us for 1, ~850us for 0
                pulses.append(2140 if bit == 1 else 850)
        
        # Trailing pulses
        pulses.extend([420, 2140, 420, 2140, 420])
        
        return pulses

    def set(self, *, power=None, mode=None, temp=None, fan=None, ifeel=None):
        """Update controller state and send a full packet for the resulting config."""
        if power is not None:
            power = str(power).lower()
            if power not in {"on", "off"}:
                raise ValueError("power must be 'on' or 'off'")
            self.state["power"] = power

        if mode is not None:
            mode = str(mode).upper()
            if mode not in {"COOL", "HEAT", "FAN"}:
                raise ValueError("mode must be 'COOL', 'HEAT', or 'FAN'")
            self.state["mode"] = mode

        if temp is not None:
            temp = int(temp)
            if not (15 <= temp <= 30):
                print(f"Temperature {temp} is out of range (15-30).")
                return False
            self.state["temp"] = temp

        if fan is not None:
            fan = str(fan).upper()
            if fan not in {"AUTO", "1", "2", "3"}:
                raise ValueError("fan must be 'AUTO', '1', '2', or '3'")
            self.state["fan"] = fan

        if ifeel is not None:
            self.state["ifeel"] = bool(ifeel)

        hour, minute = get_current_time_gmt1()
        byte_packet = generate_nibe_packet(
            hour=hour,
            minute=minute,
            power=self.state["power"],
            mode=self.state["mode"],
            temp=self.state["temp"],
            fan=self.state["fan"],
            ifeel=self.state["ifeel"],
        )

        pulses = self._bytes_to_pulses(byte_packet)
        print(
            "Sending state: "
            f"power={self.state['power']} mode={self.state['mode']} "
            f"temp={self.state['temp']} fan={self.state['fan']} "
            f"ifeel={self.state['ifeel']} at {hour:02d}:{minute:02d} (GMT+1)"
        )
        return self._send_pulses(pulses)
    
    def set_temperature(self, temp):
        """Set temperature while preserving all other state."""
        return self.set(temp=temp)

    def power_on(self):
        """Turn on the heat pump while preserving current mode/temp/fan state."""
        return self.set(power="on")

    def power_off(self):
        """Turn off the heat pump while preserving current mode/temp/fan state."""
        return self.set(power="off")

    def set_fan_auto(self):
        """Set fan to AUTO while preserving current mode/temp/power state."""
        return self.set(fan="AUTO")

    def set_mode(self, mode, fan=None):
        """Set operating mode while preserving other state values."""
        if fan is None:
            return self.set(mode=mode)
        return self.set(mode=mode, fan=fan)

    def close(self):
        if self.pi and self.pi.connected:
            self.pi.stop()


# --- Example Usage ---
if __name__ == "__main__":
    nibe = NibeController()

    try:
        if len(sys.argv) > 1:
            cmd = sys.argv[1].lower()

            if cmd == "on":
                nibe.power_on()
            elif cmd == "off":
                nibe.power_off()
            elif cmd == "auto":
                nibe.set_fan_auto()
            elif cmd.isdigit():
                nibe.set_temperature(int(cmd))
            else:
                print(
                    "Unknown command. Use: on, off, auto, or a temperature (15-30)"
                )
        else:
            print("Usage examples:")
            print("  python3 nibe_controller.py 23    (Sets temp to 23°C)")
            print("  python3 nibe_controller.py on    (Turns unit ON)")
            print("  python3 nibe_controller.py off   (Turns unit OFF)")
            print("  python3 nibe_controller.py auto  (Sets fan to AUTO)")
    finally:
        nibe.close()
