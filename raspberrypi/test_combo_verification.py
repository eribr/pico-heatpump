"""
Test för att verifiera att beräkningskod genererar samma bytes som combo-inspelningarna.

Detta test läser combo_metadata.json och jämför förväntade bytes med genererade bytes.
Använder nibe_protocol.py för byte-generering.
"""

import json
import sys
from nibe_protocol import generate_nibe_packet

def load_combo_metadata():
    """Läs combo_metadata.json"""
    with open("combo_metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)

def hex_str_to_int(hex_str):
    """Konvertera '0xAC' till 172"""
    return int(hex_str, 16)

def generate_nibe_packet_wrapper(hour, minute, power, mode, temp, fan, ifeel):
    """Wrapper som anropar nibe_protocol.generate_nibe_packet()"""
    return generate_nibe_packet(
        hour=hour,
        minute=minute,
        power=power,
        mode=mode,
        temp=temp,
        fan=fan,
        ifeel=ifeel
    )

def verify_recording(filename, expected_data, generated_data):
    """Jämför förväntad data med genererad data"""
    mismatches = []
    
    for i in range(min(len(expected_data), len(generated_data))):
        if expected_data[i] != generated_data[i]:
            mismatches.append({
                "byte_index": i,
                "expected": f"0x{expected_data[i]:02X}",
                "generated": f"0x{generated_data[i]:02X}"
            })
    
    if len(expected_data) != len(generated_data):
        mismatches.append({
            "error": "length_mismatch",
            "expected_length": len(expected_data),
            "generated_length": len(generated_data)
        })
    
    return {
        "filename": filename,
        "passed": len(mismatches) == 0,
        "mismatches": mismatches
    }

def run_tests():
    """Kör alla tester"""
    metadata = load_combo_metadata()
    recordings = metadata["recordings"]
    
    print("=" * 70)
    print("COMBO VERIFICATION TEST")
    print("=" * 70)
    print()
    print(f"Totalt antal inspelningar: {len(recordings)}")
    print()
    
    results = []
    passed_count = 0
    failed_count = 0
    
    for filename, data in sorted(recordings.items()):
        # Extrahera data från metadata JSON
        time_info = data["time"]
        settings = data["settings"]
        expected_bytes_dict = data["bytes"]
        expected_bytes = [hex_str_to_int(expected_bytes_dict[f"B{i}"]) for i in range(11)]
        
        # Mata in klockslagen och inställningar från JSON till generatorn
        generated_bytes = generate_nibe_packet_wrapper(
            hour=time_info["hour"],
            minute=time_info["minute"],
            power=settings["power"],
            mode=settings["mode"],
            temp=settings["temp"],
            fan=settings["fan"],
            ifeel=settings["ifeel"]
        )
        
        # Verifiera
        result = verify_recording(filename, expected_bytes, generated_bytes)
        results.append(result)
        
        if result["passed"]:
            passed_count += 1
            status = "[PASS]"
        else:
            failed_count += 1
            status = "[FAIL]"
        
        print(f"{status} | {filename:20} | {time_info['hour']:02d}:{time_info['minute']:02d}")
        
        if not result["passed"] and result["mismatches"]:
            # Visa första 3 mismatches
            for mismatch in result["mismatches"][:3]:
                if "byte_index" in mismatch:
                    print(f"       └─ B{mismatch['byte_index']}: expected {mismatch['expected']}, got {mismatch['generated']}")
                else:
                    print(f"       └─ {mismatch}")
    
    print()
    print("=" * 70)
    print(f"RESULTAT: {passed_count} pass, {failed_count} fail av {len(recordings)} tester")
    print("=" * 70)
    print()
    
    if failed_count == 0:
        print("*** ALLA TESTER GODKANDA!")
        print("Byte-genereringen matchar combo-inspelningarna perfekt.")
        return 0
    else:
        print("!!! IMPLEMENTERA generate_nibe_packet_placeholder() for att fixa testen.")
        print()
        print("Nästa steg:")
        print("1. Analysera byte-mönster i combo_metadata.json")
        print("2. Implementera korrekt kodning för B2-B10 baserat på inställningar och tid")
        print("3. Kör detta test igen tills alla passar")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
