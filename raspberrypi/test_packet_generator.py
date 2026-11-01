"""Compare generated Nibe packets with decoded IR recordings."""

import json
import sys
from pathlib import Path

from nibe_protocol import generate_nibe_packet


ROOT = Path(__file__).resolve().parent
METADATA_PATH = ROOT / "packet_generator_metadata.json"
BYTE_COUNT = 11


def load_metadata():
    with METADATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def expected_packet(recording):
    return [int(recording["bytes"][f"B{index}"], 16) for index in range(BYTE_COUNT)]


def run_tests():
    recordings = load_metadata()["recordings"]
    passed = 0
    failed = 0
    skipped = 0

    print("PACKET GENERATOR VERIFICATION")
    print("=" * 72)

    for name, recording in sorted(recordings.items()):
        if not recording["complete"] or len(recording["bytes"]) != BYTE_COUNT:
            byte_count = len(recording["bytes"])
            skipped += 1
            print(f"[SKIP] {name}: incomplete capture ({byte_count}/{BYTE_COUNT} bytes)")
            continue

        expected = expected_packet(recording)
        time_info = recording["time"]
        settings = recording["settings"]
        # Batch captures do not establish an hour; the generator currently requires one.
        hour = time_info["hour"] if time_info["hour"] is not None else 0
        generated = generate_nibe_packet(
            hour=hour,
            minute=time_info["minute"],
            **settings,
        )
        mismatches = [
            (index, wanted, actual)
            for index, (wanted, actual) in enumerate(zip(expected, generated))
            if wanted != actual
        ]
        if len(generated) != BYTE_COUNT:
            mismatches.append(("length", BYTE_COUNT, len(generated)))

        if mismatches:
            failed += 1
            print(f"[FAIL] {name}")
            for index, wanted, actual in mismatches:
                if index == "length":
                    print(f"       packet length: expected {wanted}, got {actual}")
                else:
                    print(f"       B{index}: expected 0x{wanted:02X}, got 0x{actual:02X}")
        else:
            passed += 1
            print(f"[PASS] {name}")

    print("=" * 72)
    print(f"RESULT: {passed} pass, {failed} fail, {skipped} skip of {len(recordings)} recordings")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run_tests())