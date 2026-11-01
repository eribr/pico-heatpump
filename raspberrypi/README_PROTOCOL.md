# Nibe IR Controller - Dynamic Generation

## Overview

The controller has been updated from static pre-recorded signals (MASTERS) to **dynamic byte generation**. Packet generation is still being verified against captured signals; the current tests show unresolved temperature, mode, and clock encodings.

## New Files

### `nibe_protocol.py`
Core module for byte generation:
- `generate_nibe_packet()` - Generates 11-byte IR packets
- `get_current_time_gmt1()` - Gets time in GMT+1 (heat pump is locked to summer time)

### `nibe_controller.py` (updated)
- Now uses `nibe_protocol.py` instead of static MASTERS
- All commands are generated dynamically with current time
- MASTERS and CONFIG kept as `_LEGACY_*` for reference

### `test_packet_generator.py`
- Compares generated packets with decoded combo and recordings-batch captures
- Reports incomplete captures separately from failed comparisons

### `packet_generator_metadata.json`
- Metadata for decoded combo and recordings-batch captures
- Stores packet bytes, annotated settings, and available clock information

## Usage

### Basic example

```python
from nibe_controller import NibeController

nibe = NibeController()

# Set temperature (uses current time automatically)
# Set the complete configuration (uses current time automatically)
nibe.set(power="on", mode="HEAT", temp=23, fan="AUTO", ifeel=False)

nibe.close()
```

### Via HTTP API (nibe_server.py)

The API uses one endpoint to set the complete heat pump state:

```bash
curl -u :password \
    -H 'Content-Type: application/json' \
    -X POST http://raspberry-pi:5000/api/set \
    -d '{"power":"on","mode":"HEAT","temp":23,"fan":"AUTO","ifeel":false}'
```

## Time Encoding and DST

The controller supplies GMT+1 hour and minute values to the generator. The current generator does not use `hour`; its B4/B8 clock encoding is not verified across both capture groups. The batch recordings have no reliable hour annotation, and their B4 value differs from the combo captures.

## Byte Protocol (simplified)

```
B0-B1:  0xAC 0xF5           (header)
B2:     Mode/temperature
B3:     Fan/temperature details
B4:     Unresolved; combo captures use 0x0A/0x1A, batch captures use 0x0E
B5-B6:  0xE0 0x00           (constant)
B7:     Mode-specific code
B8:     Candidate minute in bits 2-7; batch hour is unavailable
B9:     Power/IFeel
B10:    Checksum
```

The 35 complete captures all match the observed checksum formula
`(sum(B0:B9) * 4 + 0x0A) & 0xFF`. The generator currently uses a different
formula that skips B2 and adds `0x8A`.

## Testing and Verification

Run the packet-generator verification:
```bash
python test_packet_generator.py
```

## Current Verification Findings

The current run reports **12 pass, 23 fail, and 1 skipped** across 36 metadata
entries. All 12 passes are complete combo captures; all 19 batch captures fail
with the current generator. `combo/fan_1.json` is only 3 of 11 bytes and is
skipped as incomplete.

The failures are not limited to checksum calculation:
- Updating B10 to the observed checksum formula removed four combo failures;
    the formula matches all 35 complete captured packets.
- Remaining combo payload mismatches include B2 for `cold_moisture` and
    `heat_2`, and B7 for `ifeel` and `no_ifeel`.
- All batch temperature captures have B2/B3/B7 combinations that the current
    generator cannot produce with any documented mode/fan combination at the
    labeled temperature. Batch settings still leave other operating modes
    unknown.
- Batch B4 is consistently `0x0E`, unlike combo B4 (`0x0A`/`0x1A`), and the
    current B8 formula does not reproduce the batch captures. The hour argument
    is currently unused.

These results establish mismatches against the captures, but do not yet
distinguish unsupported settings from incorrect annotations for every batch
recording.

Test protocol module:
```bash
python nibe_protocol.py
```

## Migration from Old System

### Before (MASTERS)
```python
# Static pre-recorded signals
MASTERS = {
    "22": [6365, 3205, 410, 865, ...],  # Thousands of values
    ...
}

CONFIG = {
    22: {"base": "22", "flips": []},
    23: {"base": "22", "flips": [22, 88, 89]},
    ...
}

nibe.set(power="on", mode="HEAT", temp=23, fan="AUTO", ifeel=False)
```

### Now (Dynamic generation)
```python
# Generates bytes dynamically based on time and settings
packet = generate_nibe_packet(
    hour=23,
    minute=10,
    temp=23,
    power="on"
)  # Returns [0xAC, 0xF5, 0xE0, ...]

nibe.set(power="on", mode="HEAT", temp=23, fan="AUTO", ifeel=False)
```

## Advantages of Dynamic Generation

✅ **Works year-round** - No DST issues  
✅ **Less code** - No MASTERS database with thousands of values  
✅ **Flexible** - Easy to add new temperatures and modes  
✅ **Testable** - Verifiable against recordings  
✅ **Understandable** - Encoding is documented and clear  

## Next Steps

If new temperatures or modes are needed:
1. Record new commands
2. Analyze bytes with existing tools in `util/`
3. Update `generate_nibe_packet()` in `nibe_protocol.py`
4. Add decoded capture metadata to `packet_generator_metadata.json`
5. Verify with `test_packet_generator.py`

## Support

For questions or issues, see:
- `packet_generator_metadata.json` - Decoded capture test data
- `nibe_protocol.py` - Core byte generation logic
- `test_packet_generator.py` - Packet-generator verification

## License

Same as main project.
