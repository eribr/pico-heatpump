# models/nibe_aa.py

class NibeAAHeatpumpIR:
    def __init__(self):
        pass

    def calculate_checksum(self, data):
        # Checksumman är summan av de första 8 byten MOD 256
        return sum(data[:8]) & 0xFF

    def send(self, ir_driver, power, temp):
        # Template: 9 bytes
        # Byte 0-1 är ofta ID, t.ex. 0x23, 0xCB
        packet = bytearray([0x23, 0xCB, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])

        # Power & Mode (Exempel: Heat = 0x04)
        # Om power är 0, skicka power-off bit
        if power:
            packet[2] = 0x04 # Mode Heat
            packet[3] = 0x01 # Power On
        else:
            packet[3] = 0x00 # Power Off

        # Temperatur (ofta temp - 8 eller liknande)
        # Enligt Nibe_AA-standard:
        packet[4] = uint8(temp - 8) if hasattr(self, 'uint8') else (temp - 8)

        # Beräkna checksumma och lägg i sista byten
        packet[8] = self.calculate_checksum(packet)

        ir_driver.send_ir(packet)
