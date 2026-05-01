# models/argo.py

class ArgoHeatpumpIR:
    def __init__(self):
        # Standardinställningar för Argo
        pass

    def send(self, ir_driver, power, mode, fan, temp, swing):
        # 12-byte template för Argo
        # Byte 0-1 är ofta tillverkarens ID: 0x25, 0x15
        packet = bytearray([0x25, 0x15, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        # Byte 2: Power och Mode
        # Power: 0=Off, 1=On. Mode: 0=Auto, 1=Cool, 2=Dry, 3=Heat, 4=Fan
        mode_val = {"AUTO": 0, "COOL": 1, "DRY": 2, "HEAT": 3, "FAN": 4}.get(mode.upper(), 3)
        packet[2] = (power & 0x01) | (mode_val << 4)

        # Byte 3: Temperatur
        # Argo använder ofta temp rakt av, men offset kan variera. 
        # Här sätter vi temp mellan 10-32.
        packet[3] = max(10, min(32, temp))

        # Byte 4: Fläkt (Fan)
        # 0=Auto, 1=Low, 2=Med, 3=High
        fan_val = {"AUTO": 0, "LOW": 1, "MED": 2, "HIGH": 3}.get(fan.upper(), 0)
        packet[4] = fan_val

        # Byte 5: Swing
        # 0=Off, 1=On
        packet[5] = 1 if swing else 0

        # Byte 11: Checksum (XOR på alla tidigare bytes)
        checksum = 0
        for i in range(11):
            checksum ^= packet[i]
        packet[11] = checksum

        ir_driver.send_ir(packet)