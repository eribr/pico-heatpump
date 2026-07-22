import glob
import json
import os


def decode_pulse_distance(raw_data):
    if len(raw_data) < 4 or raw_data[0] < 4000:
        return None
    bits = []
    for i in range(2, len(raw_data) - 1, 2):
        space = raw_data[i + 1]
        bits.append(1 if space > 1500 else 0)

    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i : i + 8]
        if len(byte_bits) == 8:
            val = sum(bit << bit_idx for bit_idx, bit in enumerate(byte_bits))
            bytes_list.append(val)
    return bytes_list


def calculate_argo_checksum(payload):
    # Summera alla bytes utom index 2 (Byte 3) och index 10 (Checksumman)
    bytes_to_sum = payload[0:2] + payload[3:10]
    return (sum(bytes_to_sum) * 4 + 0x8A) & 0xFF


def main():
    files = glob.glob("recordings_batch/*.json")
    print(f"{'Filnamn':15} | {'Förväntad':10} | {'Beräknad':10} | Status")
    print("-" * 50)

    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        with open(filepath, "r") as f:
            raw = json.load(f)
            data = decode_pulse_distance(raw)
            if data and len(data) >= 11:
                expected = data[10]
                calculated = calculate_argo_checksum(data)
                match = "OK" if expected == calculated else "FEL"
                print(
                    f"{filename:15} | 0x{expected:02X}       | 0x{calculated:02X}       | {match}"
                )


if __name__ == "__main__":
    main()