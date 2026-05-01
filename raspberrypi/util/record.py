import pigpio
import time
import json

INPUT_PIN = 18
pi = pigpio.pi()
pi.set_mode(INPUT_PIN, pigpio.INPUT)

recording = []
last_tick = None

def callback(gpio, level, tick):
    global last_tick
    if last_tick is not None:
        diff = pigpio.tickDiff(last_tick, tick)
        recording.append(diff)
    last_tick = tick

print("Gör dig redo... Tryck på knappen på fjärrkontrollen NU.")
cb = pi.callback(INPUT_PIN, pigpio.EITHER_EDGE, callback)

# Vänta 2 sekunder på att signalen ska landa
time.sleep(2)
cb.cancel()

if len(recording) > 10:
    filename = input("Vad ska vi döpa detta kommando till? (t.ex. on_20_heat): ") + ".json"
    with open(filename, 'w') as f:
        json.dump(recording, f)
    print(f"Sparat {len(recording)} pulser till {filename}")
else:
    print("Fångade ingen signal. Prova igen och håll fjärren närmare.")

pi.stop()