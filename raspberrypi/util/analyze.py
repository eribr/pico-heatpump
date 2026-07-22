import glob
import json
import os


def decode_pulse_distance(raw_data):
    """Avkodar raw microsecond timings till bitar och sedan till bytes."""
    # Kolla att vi har en header (brukar vara ca 6000us mark + 3000us space)
    if len(raw_data) < 4 or raw_data[0] < 4000:
        return None

    bits = []
    # Hoppa över headern (index 0 och 1) och stegra i par (mark, space)
    for i in range(2, len(raw_data) - 1, 2):
        mark = raw_data[i]
        space = raw_data[i + 1]

        # En normal bit har mark på ~450us.
        # Om space är ca 800us = 0, om space är ca 2100us = 1.
        if space > 1500:
            bits.append(1)
        else:
            bits.append(0)

    # Omvandla bitar till bytes (IR-protokoll skickar oftast LSB först)
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i : i + 8]
        if len(byte_bits) == 8:
            val = 0
            for bit_idx, bit in enumerate(byte_bits):
                val |= bit << bit_idx  # LSB first
            bytes_list.append(val)

    return bytes_list


def test_checksum_algorithms(all_recordings):
    """Testar olika checksumme-uträkningar mot sista byten i varje fil."""
    print("\n--- TESTAR CHECKSUMME-ALGORITMER ---")

    algorithms = [
        ("Summa modulo 256 (sum & 0xFF)", lambda b: sum(b) & 0xFF),
        (
            "Inverterad summa ((0xFF - sum) & 0xFF)",
            lambda b: (0xFF - sum(b)) & 0xFF,
        ),
        (
            "Argo/Gree special ((0x55 - sum) & 0xFF)",
            lambda b: (0x55 - sum(b)) & 0xFF,
        ),
        (
            "Argo typ 2 ((sum - 0x55) & 0xFF)",
            lambda b: (sum(b) - 0x55) & 0xFF,
        ),
        ("XOR av alla bytes", lambda b: eval(" ^ ".join(map(str, b)))),
    ]

    for name, func in algorithms:
        success_count = 0
        for filename, data in all_recordings.items():
            payload = data[:-1]  # Alla bytes utom den sista
            actual_checksum = data[-1]  # Sista byten är (oftast) checksumman

            try:
                calculated = func(payload)
                if calculated == actual_checksum:
                    success_count += 1
            except Exception:
                pass

        if success_count == len(all_recordings):
            print(
                f"[BINGO!] '{name}' stämmer för ALLA {len(all_recordings)} filer!"
            )
        elif success_count > 0:
            print(
                f"[DELVIS] '{name}' stämmer för {success_count}/{len(all_recordings)} filer."
            )
        else:
            print(f"[NEJ]    '{name}' gav ingen träff.")


def main():
    folder_path = "recordings_batch/*.json"
    files = glob.glob(folder_path)

    if not files:
        print(f"Hittade inga filer i {folder_path}")
        return

    print(f"Hittade {len(files)} inspelningar. Avkodar...\n")

    all_recordings = {}

    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        with open(filepath, "r") as f:
            try:
                raw_data = json.load(f)
                decoded_bytes = decode_pulse_distance(raw_data)

                if decoded_bytes:
                    all_recordings[filename] = decoded_bytes
                    # Skriv ut utskrift i Hex-format
                    hex_str = " ".join([f"{b:02X}" for b in decoded_bytes])
                    print(f"{filename:15} | {hex_str}")
                else:
                    print(f"{filename:15} | Kunde inte avkoda (för kort/brus)")
            except Exception as e:
                print(f"{filename:15} | Fel vid läsning: {e}")

    if all_recordings:
        test_checksum_algorithms(all_recordings)
    else:
        print("Inga giltiga inspelningar att analysera.")


if __name__ == "__main__":
    main()
