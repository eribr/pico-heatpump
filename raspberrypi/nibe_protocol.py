"""
Nibe IR Protocol - Byte Generator

Dynamisk generering av Nibe IR-paket baserat på reverse engineering av inspelningar.
Ersätter statiska MASTERS med dynamisk kodning.
"""


def generate_nibe_packet(hour, minute, power="on", mode=None, temp=None, fan=None, ifeel=False):
    """
    Generera Nibe IR-paket (11 bytes) baserat på inställningar och tid.
    
    Args:
        hour: Timme (0-23) - använd alltid GMT+1 för att matcha pumpen
        minute: Minut (0-59)
        power: "on" eller "off"
        mode: "COOL", "HEAT", "FAN", eller None
        temp: Temperatur (15-30) eller None
        fan: "AUTO", "1", "2", "3", eller None
        ifeel: True/False
    
    Returns:
        Lista med 11 bytes [B0..B10]
    
    Examples:
        >>> generate_nibe_packet(14, 30, temp=23)  # 23°C kl 14:30
        >>> generate_nibe_packet(23, 10, power="off")  # Stäng av
        >>> generate_nibe_packet(12, 45, mode="HEAT", fan="AUTO")
    """
    # B0-B1: Konstant header
    packet = [0xAC, 0xF5, 0x00, 0x00, 0x00, 0xE0, 0x00, 0x00, 0x00, 0x00, 0x00]
    
    # B2: Mode och temperatur
    if temp == 22:
        packet[2] = 0xA0
    elif temp == 23:
        packet[2] = 0xE0
    elif temp == 24:
        packet[2] = 0x20
    elif temp == 21:
        packet[2] = 0x60
    elif temp == 25:
        packet[2] = 0x20
    elif mode == "COOL":
        packet[2] = 0x50 if fan == "AUTO" else 0x40
    elif mode == "HEAT":
        if fan == "AUTO":
            packet[2] = 0x68
        else:
            packet[2] = 0x70
    elif mode == "FAN":
        packet[2] = 0x60
    else:
        packet[2] = 0x60  # Default
    
    # B3: Fan speed och temperatur-relaterat
    if temp == 24:
        packet[3] = 0x45
    elif temp in [22, 23]:
        packet[3] = 0x44
    elif fan == "2":
        packet[3] = 0x54
    elif fan == "3":
        packet[3] = 0x5C
    elif mode == "COOL" or (mode is None and temp is None):
        packet[3] = 0x64
    else:
        packet[3] = 0x44
    
    # B4: Tid-relaterat (varierar med minut)
    # Observerat: 0x0A för jämna minuter, 0x1A för udda
    packet[4] = 0x1A if (minute % 2 == 1) else 0x0A
    
    # B5-B6: Konstant (redan satt)
    
    # B7: Mode-specifik kod
    if temp == 22:
        packet[7] = 0xCF
    elif temp in [23, 24]:
        packet[7] = 0xD7
    elif mode == "FAN":
        packet[7] = 0xDF
    elif mode == "HEAT":
        packet[7] = 0xEF
    elif mode == "COOL":
        packet[7] = 0xFF if fan == "AUTO" else 0xF7
    elif power == "on" and mode is None:
        packet[7] = 0x0F
    else:
        packet[7] = 0x07
    
    # B8: Minuter kodade i höga 6 bitar
    # Formel: minut 10 → 0x2B, minut 11 → 0x2C
    if minute == 10:
        packet[8] = 0x2B
    elif minute == 11:
        packet[8] = 0x2C
    else:
        # Generisk formel
        low_bits = 0x03 if (minute % 2 == 0) else 0x00
        packet[8] = (minute << 2) | low_bits
    
    # B9: Power och IFeel
    if power == "off":
        packet[9] = 0x10
    elif ifeel:
        packet[9] = 0xB0
    else:
        packet[9] = 0x30
    
    # B10: Checksumma
    # Formel: (sum(B0:B1 + B3:B9) * 4 + 0x8A) & 0xFF
    # OBS: Skippar B2!
    bytes_to_sum = packet[0:2] + packet[3:10]
    packet[10] = (sum(bytes_to_sum) * 4 + 0x8A) & 0xFF
    
    return packet


def get_current_time_gmt1():
    """
    Hämta aktuell tid i GMT+1 (sommartid).
    Pumpen är låst på sommartid och byter aldrig.
    
    Returns:
        tuple: (hour, minute)
    """
    import time
    
    # Hämta UTC tid och lägg till 1 timme
    utc_time = time.gmtime()
    hour = (utc_time.tm_hour + 1) % 24
    minute = utc_time.tm_min
    
    return hour, minute


if __name__ == "__main__":
    # Test
    print("Testing Nibe Protocol Generator")
    print("=" * 60)
    
    # Test några kombinationer
    test_cases = [
        {"desc": "Temp 22°C, 14:30", "hour": 14, "minute": 30, "temp": 22},
        {"desc": "Temp 23°C, 10:00", "hour": 10, "minute": 0, "temp": 23},
        {"desc": "Power off, 23:11", "hour": 23, "minute": 11, "power": "off"},
        {"desc": "Heat AUTO, 12:45", "hour": 12, "minute": 45, "mode": "HEAT", "fan": "AUTO"},
    ]
    
    for tc in test_cases:
        desc = tc.pop("desc")
        packet = generate_nibe_packet(**tc)
        hex_str = " ".join(f"{b:02X}" for b in packet)
        print(f"{desc:25} | {hex_str}")
    
    print()
    print("Current time (GMT+1):", get_current_time_gmt1())
