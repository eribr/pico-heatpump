# Pico Heat Pump Controller

A MicroPython project for controlling Nibe heat pumps using infrared (IR) signals on the Raspberry Pi Pico.

## Overview

This project provides a complete solution for controlling Nibe brand heat pumps through IR communication. It includes:

- IR driver for sending commands to the heat pump
- Nibe-specific heat pump IR protocol implementation
- Configuration constants for all supported modes and settings
- Example main loop for continuous operation

## Features

- **Power Control**: Turn the heat pump on/off
- **Operating Modes**: Auto, Heat, Cool, Dry, Fan
- **Fan Speed Control**: Auto, 4 levels, Silent mode
- **Temperature Setting**: 10°C to 32°C range
- **Vertical Swing Control**: Auto, Swing, and fixed positions
- **Turbo Mode**: Enhanced performance mode
- **I-Feel Mode**: Room temperature sensing

## Hardware Requirements

- Raspberry Pi Pico (or compatible MicroPython board)
- IR LED connected to a GPIO pin (default: "LED" pin)
- Nibe brand heat pump with IR remote control

## Installation

1. Copy all files to your Raspberry Pi Pico using Thonny, PyMakr, or your preferred MicroPython IDE.

2. Ensure the IR LED is connected to the pin specified in `config.py` (default: "LED").

## Configuration

Edit `config.py` to customize:

- `IR_PIN`: The GPIO pin connected to your IR LED
- Other timing constants if needed for your specific setup

## Usage

Run `main.py` to start the controller. The example code demonstrates sending a heat command at 21°C with auto fan speed.

```python
from models.nibe import NibeHeatpumpIR, POWER_ON, MODE_HEAT, FAN_AUTO, VDIR_AUTO
from ir_driver import IRDriver
from config import IR_PIN

# Initialize IR driver
ir_driver = IRDriver(IR_PIN)
ir_driver.set_frequency(38)

# Initialize heat pump interface
nibe_ir = NibeHeatpumpIR()

# Send a command
nibe_ir.send(ir_driver, POWER_ON, MODE_HEAT, FAN_AUTO, 21, VDIR_AUTO, VDIR_AUTO)
```

### Available Commands

- **Power**: `POWER_ON`, `POWER_OFF`
- **Modes**: `MODE_AUTO`, `MODE_HEAT`, `MODE_COOL`, `MODE_DRY`, `MODE_FAN`
- **Fan Speeds**: `FAN_AUTO`, `FAN_4`, `FAN_3`, `FAN_2`, `FAN_SILENT`
- **Vertical Directions**: `VDIR_AUTO`, `VDIR_SWING`, `VDIR_UP`, `VDIR_MUP`, `VDIR_MIDDLE`, `VDIR_MDOWN`, `VDIR_DOWN`

## Project Structure

- `main.py`: Main entry point with example usage
- `ir_driver.py`: Low-level IR signal transmission
- `models/nibe.py`: Nibe heat pump IR protocol implementation
- `config.py`: Configuration constants and settings
- `utils.py`: Utility functions for bit manipulation
- `blink.py`: Simple LED blink test program

## IR Code Origin

The IR protocol implementation is a conversion from the Arduino library [arduino-heatpumpir](https://github.com/ToniA/arduino-heatpumpir) by ToniA, adapted for MicroPython and the Raspberry Pi Pico.

## License

This project is licensed under the GNU General Public License v2.0 (GPL-2.0).

## Disclaimer

This software is provided as-is without warranty. Use at your own risk. Ensure compliance with your heat pump manufacturer's guidelines and local regulations.