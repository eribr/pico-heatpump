import json
import os

MASTER = "temp_22.json"

def get_bits(filename):
    with open(filename, 'r') as f:
        pulses = json.load(f)
    return ["1" if pulses[i] > 1500 else "0" for i in range(3, len(pulses), 2)]

master_bits = get_bits(MASTER)
files = sorted([f for f in os.listdir('.') if f.startswith('temp_') and f.endswith('.json')])

print(f"{'Temperatur':<12} | {'Ändrade Bit-index (relativt master 22C)':<30}")
print("-" * 50)

for f in files:
    if f == MASTER: continue
    current_bits = get_bits(f)
    diffs = [i for i in range(len(master_bits)) if master_bits[i] != current_bits[i]]
    temp_val = f.replace('temp_', '').replace('.json', '')
    print(f"{temp_val:<12} | {diffs}")