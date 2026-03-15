import ir_driver
import time
from models.nibe import NibeHeatpumpIR, POWER_ON, MODE_HEAT, FAN_AUTO, VDIR_AUTO
from ir_driver import IRDriver
from config import IR_PIN

def main():
    # Initialize the IR driver (pass the pin used for the IR LED)
    ir_driver = IRDriver(IR_PIN)
    ir_driver.set_frequency(38)

    # Initialize the Nibe heat pump IR interface
    nibe_ir = NibeHeatpumpIR()

    # Main loop
    while True:
        print("Start loop")
        # Example: Send a command to the heat pump
        # Note: the send() API expects both vertical and horizontal swing args.
        nibe_ir.send(ir_driver, POWER_ON, MODE_HEAT, FAN_AUTO, 21, VDIR_AUTO, VDIR_AUTO)

        # Wait for a specified interval before sending the next command
        print("Sleep")
        time.sleep(1)
        print("New loop")

if __name__ == "__main__":
    main()