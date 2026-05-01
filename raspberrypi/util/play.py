import pigpio
import time
import json

IR_PIN = 17
pi = pigpio.pi()
pi.set_mode(IR_PIN, pigpio.OUTPUT)

def play_command(filename):
    with open(filename, 'r') as f:
        pulses = json.load(f)

    pi.wave_clear()
    wave_pulses = []
    
    # Varannan puls är Mark (38kHz), varannan är Space (tyst)
    for i, microsecs in enumerate(pulses):
        if i % 2 == 0: # Mark (Active Low mottagare -> Vi skickar High)
            # Skapa 38kHz bärvåg
            cycles = int(microsecs / 26)
            for _ in range(cycles):
                wave_pulses.append(pigpio.pulse(1<<IR_PIN, 0, 13))
                wave_pulses.append(pigpio.pulse(0, 1<<IR_PIN, 13))
        else: # Space
            wave_pulses.append(pigpio.pulse(0, 1<<IR_PIN, microsecs))

    pi.wave_add_generic(wave_pulses)
    wid = pi.wave_create()
    if wid >= 0:
        pi.wave_send_once(wid)
        while pi.wave_tx_busy():
            time.sleep(0.05)
        pi.wave_delete(wid)
        print(f"Spelade upp {filename}!")

filename = input("Vilken fil vill du spela upp? ")
play_command(filename)
pi.stop()