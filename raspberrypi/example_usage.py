"""
Exempel på hur man använder den nya dynamiska Nibe IR-controllern
"""

# För test på Windows (utan pigpio)
import sys
import types
sys.modules.setdefault('pigpio', types.ModuleType('pigpio'))

from nibe_controller import NibeController
from nibe_protocol import get_current_time_gmt1

def main():
    print("=" * 60)
    print("Nibe IR Controller - Dynamic Generation Example")
    print("=" * 60)
    print()
    
    # Visa aktuell tid (GMT+1 - matchar pumpen)
    hour, minute = get_current_time_gmt1()
    print(f"Current time (GMT+1): {hour:02d}:{minute:02d}")
    print()
    
    # OBS: På Windows kommer detta att misslyckas eftersom pigpiod inte körs
    # På Raspberry Pi med pigpiod igång fungerar det!
    
    print("Example commands (would execute on Raspberry Pi):")
    print()
    
    # Exempel 1: Sätt temperatur
    print("1. Set temperature to 23°C")
    print("   nibe.set_temperature(23)")
    print()
    
    # Exempel 2: Stäng av
    print("2. Turn off")
    print("   nibe.power_off()")
    print()
    
    # Exempel 3: Sätt mode
    print("3. Set to HEAT mode with AUTO fan")
    print("   nibe.set_mode('HEAT', fan='AUTO')")
    print()
    
    # Exempel 4: Fläkt auto
    print("4. Set fan to AUTO")
    print("   nibe.set_fan_auto()")
    print()
    
    print("=" * 60)
    print("All commands now use dynamic generation instead of static")
    print("MASTERS, and automatically include current time in GMT+1!")
    print("=" * 60)

if __name__ == "__main__":
    main()
