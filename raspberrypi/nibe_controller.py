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

    def set(self, *, power, mode, temp, fan, ifeel):
        """Send a packet containing the complete heat pump configuration."""
        power = str(power).lower()
        if power not in {"on", "off"}:
            raise ValueError("power must be 'on' or 'off'")

        mode = str(mode).upper()
        if mode not in {"COOL", "HEAT", "FAN"}:
            raise ValueError("mode must be 'COOL', 'HEAT', or 'FAN'")

        try:
            temp = int(temp)
        except (TypeError, ValueError) as exc:
            raise ValueError("temp must be an integer from 15 to 30") from exc
        if not (15 <= temp <= 30):
            raise ValueError("temp must be an integer from 15 to 30")

        fan = str(fan).upper()
        if fan not in {"AUTO", "1", "2", "3"}:
            raise ValueError("fan must be 'AUTO', '1', '2', or '3'")

        if not isinstance(ifeel, bool):
            raise ValueError("ifeel must be a boolean")

        hour, minute = get_current_time_gmt1()
        byte_packet = generate_nibe_packet(
            hour=hour,
            minute=minute,
            power=power,
            mode=mode,
            temp=temp,
            fan=fan,
            ifeel=ifeel,
        )

        pulses = self._bytes_to_pulses(byte_packet)
        print(
            "Sending configuration: "
            f"power={power} mode={mode} temp={temp} fan={fan} "
            f"ifeel={ifeel} at {hour:02d}:{minute:02d} (GMT+1)"
        )
        return self._send_pulses(pulses)

    def close(self):
        if self.pi and self.pi.connected:
            self.pi.stop()


# --- Example Usage ---
if __name__ == "__main__":
    nibe = NibeController()

    try:
        if len(sys.argv) != 6:
            print(
                "Usage: python3 nibe_controller.py "
                "<power> <mode> <temp> <fan> <ifeel:true|false>"
            )
        else:
            ifeel_arg = sys.argv[5].lower()
            if ifeel_arg not in {"true", "false"}:
                raise ValueError("ifeel must be 'true' or 'false'")
            nibe.set(
                power=sys.argv[1],
                mode=sys.argv[2],
                temp=sys.argv[3],
                fan=sys.argv[4],
                ifeel=ifeel_arg == "true",
            )
    finally:
        nibe.close()
