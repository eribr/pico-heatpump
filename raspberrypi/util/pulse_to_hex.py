import json
import os

# Inställning: Vilken mapp ska vi skanna? 
# '.' betyder aktuell mapp, eller ange 'recordings_batch'
FOLDER_PATH = "recordings_batch" 

def pulses_to_hex(filename):
    with open(filename, 'r') as f:
        pulses = json.load(f)
    
    binary = ""
    # Hoppa över Header och läs Spaces (index 3, 5, 7...)
    for i in range(3, len(pulses), 2):
        space = pulses[i]
        binary += "1" if space > 1500 else "0"
    
    bytes_list = []
    # Dela upp i bytes (8 bitar per byte), LSB först
    for i in range(0, len(binary) - (len(binary) % 8), 8):
        byte_str = binary[i:i+8]
        bytes_list.append(int(byte_str[::-1], 2))
    
    return bytes_list

# Hämta alla .json-filer i mappen
files = [f for f in os.listdir(FOLDER_PATH) if f.endswith('.json')]
# Sortera dem (så att temp_19 kommer före temp_20)
files.sort()

print(f"{'Filnamn':<20} | {'Hex-data':<35} | Summa")
print("-" * 70)

for f in files:
    full_path = os.path.join(FOLDER_PATH, f)
    try:
        h = pulses_to_hex(full_path)
        if not h:
            continue
            
        hex_string = " ".join([f"{b:02X}" for b in h])
        
        # Beräkna en vanlig enkel checksumma (SUM MOD 256)
        # Vi tar alla bytes utom den sista
        checksum_calc = sum(h[:-1]) & 0xFF
        
        # Skriv ut resultatet snyggt i kolumner
        print(f"{f:<20} | {hex_string:<35} | {checksum_calc:02X}")
        
    except Exception as e:
        print(f"Kunde inte läsa {f}: {e}")
