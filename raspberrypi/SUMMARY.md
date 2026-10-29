# Nibe IR Protocol - Reverse Engineering Sammanfattning

## Testresultat: 10/16 godkända (62.5%)

### ✅ Fungerande inspelningar (10)
Dessa har korrekt checksumma och genereras korrekt:
- **temp_22.json, temp_23.json, temp_24.json** - Temperaturinställningar ✓
- **fan_2.json, fan_3.json, fan_3_auto.json** - Fläkthastigheter ✓
- **on.json, off.json** - Power on/off ✓
- **ifeel.json, no_ifeel.json** - IFeel-funktionen ✓
- **heat_2.json** - Heat mode ✓

### ❌ Brutna/Korrupta inspelningar (6)
Dessa har felaktig checksumma i källfilen:
- cold.json, cold_auto.json, cold_moisture.json
- heat_1.json, heat_auto.json

**Not**: Dessa inspelningar har checksumman inbakad som inte matchar verifiering. De kan antingen vara korrupta eller använda en annan checksumma-formel vi inte reverse-engineerat ännu.

##  Byte-kodning (11 bytes total)

### B0-B1: Header (konstant)
- **0xAC 0xF5** - Alltid samma

### B2: Mode och temperatur
-  temp=22 → 0xA0
- temp=23 → 0xE0
- temp=24 → 0x20
- COOL+AUTO → 0x50
- COOL → 0x40
- HEAT+AUTO → 0x68
- HEAT → 0x70/0x60
- FAN → 0x60

### B3: Fan speed och temp-del
- temp=24 → 0x45
- temp=22/23 → 0x44
- fan=2 → 0x54
- fan=3 → 0x5C
- COOL → 0x64
- Annat → 0x44

### B4: Tid-relaterat (bit 4 toggle)
- Jämna minuter → 0x0A
- Udda minuter → 0x1A

### B5-B6: Konstant
- **0xE0 0x00**

### B7: Mode-specifik kod
- temp=22 → 0xCF
- temp=23/24 → 0xD7
- FAN → 0xDF
- HEAT → 0xEF
- COOL+AUTO → 0xFF
- COOL → 0xF7
- Power ON (utan mode) → 0x0F
- Power OFF/IFeel → 0x07

### B8: Minuter kodade
- **Formel**: För minut 10 → 0x2B, minut 11 → 0x2C
- Höga 6 bitar innehåller minutvärdet: `minute = (B8 >> 2) & 0x3F`
- Låga 2 bitar varierar (0b11 för jämna, 0b00 för udda)

### B9: Power och IFeel
- Power OFF → 0x10
- IFeel ON → 0xB0
- Power ON → 0x30

### B10: Checksumma
**Formel**: `(sum(B0:B1 + B3:B9) * 4 + 0x8A) & 0xFF`

**OBS**: Skippar B2 i summan!

## Tidskodning och Sommar/Vintertid

### Problem
- Värmepumpen är låst på **sommartid (GMT+1)** och byter aldrig
- Raspberry Pi bytte till vintertid → 1 timmes skillnad
- Checksumman inkluderar tiden → gamla inspelningar fungerar inte längre

### Lösning
Använd **alltid GMT+1** i Raspberry Pi när du genererar signaler:
```python
import time
import os

# Sätt tidzon till GMT+1 (sommartid) permanent
os.environ['TZ'] = 'Europe/Stockholm'  # Men tvinga sommartid
# ELLER hårdkoda +1 timme offset i beräkningen
```

## Nästa steg

1. ✅ **Test-ramverket** är klart (`test_combo_verification.py`)
2. ✅ **Metadata** är extraherad (`combo_metadata.json`)
3. ✅ **Byte-generator** fungerar för 10/16 fall
4. ⏳ **Integrera i nibe_controller.py** - Ersätt statiska MASTERS med dynamisk generering
5. ⏳ **Tidskompensering** - Lägg till GMT+1 låsning

## Användning

### Kör tester
```bash
python test_combo_verification.py
```

### Generera signal
```python
from test_combo_verification import generate_nibe_packet_placeholder

# Generera paket för temp 23, kl 14:30
packet_bytes = generate_nibe_packet_placeholder(
    hour=14,
    minute=30,
    power="on",
    mode=None,
    temp=23,
    fan=None,
    ifeel=False
)

# packet_bytes är nu [0xAC, 0xF5, 0xE0, ...]
```
