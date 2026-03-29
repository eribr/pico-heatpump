# Pico Heat Pump Controller

A MicroPython project for controlling Nibe heat pumps using infrared (IR) signals on the Raspberry Pi Pico with WiFi web server functionality.

## Overview

This project provides a complete solution for controlling Nibe brand heat pumps through IR communication. It includes:

- IR driver for sending commands to the heat pump
- Nibe-specific heat pump IR protocol implementation
- WiFi connectivity and web server
- REST API for remote control
- HTTP Basic Authentication
- Configuration via JSON file

## Features

- **Power Control**: Turn the heat pump on/off
- **Operating Modes**: Auto, Heat, Cool, Dry, Fan
- **Fan Speed Control**: Auto, 4 levels, Silent mode
- **Temperature Setting**: 10°C to 32°C range
- **Vertical Swing Control**: Auto, Swing, and fixed positions
- **Turbo Mode**: Enhanced performance mode
- **I-Feel Mode**: Room temperature sensing
- **Web Server**: REST API with HTTP Basic Authentication
- **WiFi Connectivity**: Connect to local network

## Hardware Requirements

- Raspberry Pi Pico W (with WiFi) or compatible MicroPython board
- IR LED connected to a GPIO pin (default: "LED" pin)
- Nibe brand heat pump with IR remote control

## Configuration

Create a `config.json` file in the project root with the following structure:

```json
{
  "wifi": {
    "ssid": "your_wifi_ssid",
    "password": "your_wifi_password"
  },
  "auth": {
    "username": "admin",
    "password": "password123"
  },
  "server": {
    "port": 80
  },
  "hardware": {
    "ir_pin": "LED"
  }
}
```

## Usage

Run `main.py` to start the web server. The device will:

1. Connect to the configured WiFi network
2. Start a web server on the configured port
3. Display the IP address for API access

## REST API

The server provides a REST API with the following endpoints. All PUT endpoints require HTTP Basic Authentication using the credentials from `config.json`.

### Status
- `GET /api/status` - Get server status

### Power Control
- `PUT /api/power/on` - Turn heat pump on
- `PUT /api/power/off` - Turn heat pump off

### Operating Modes
- `PUT /api/mode/auto` - Set to Auto mode
- `PUT /api/mode/heat` - Set to Heat mode
- `PUT /api/mode/cool` - Set to Cool mode
- `PUT /api/mode/dry` - Set to Dry mode
- `PUT /api/mode/fan` - Set to Fan mode

### Fan Speed
- `PUT /api/fan/auto` - Set fan to Auto
- `PUT /api/fan/4` - Set fan to speed 4 (highest)
- `PUT /api/fan/3` - Set fan to speed 3
- `PUT /api/fan/2` - Set fan to speed 2
- `PUT /api/fan/silent` - Set fan to Silent mode

### Temperature
- `PUT /api/temp/{temperature}` - Set temperature (10-32°C)
  - Example: `PUT /api/temp/21`

### Vertical Swing
- `PUT /api/swing/auto` - Set swing to Auto
- `PUT /api/swing/swing` - Enable swing mode
- `PUT /api/swing/up` - Fixed up position
- `PUT /api/swing/mup` - Fixed middle-up position
- `PUT /api/swing/middle` - Fixed middle position
- `PUT /api/swing/mdown` - Fixed middle-down position
- `PUT /api/swing/down` - Fixed down position

### API Examples

Using curl with authentication:

```bash
export CRED=admin:password123
# Turn on the heat pump
curl -X PUT -u $CRED http://192.168.1.100/api/power/on

# Set temperature to 22°C
curl -X PUT -u $CRED http://192.168.1.100/api/temp/22

# Set to cool mode
curl -X PUT -u $CRED http://192.168.1.100/api/mode/cool

# Set fan to silent
curl -X PUT -u $CRED http://192.168.1.100/api/fan/silent
```

All API responses are in JSON format:

```json
{"power": "on", "message": "Heat pump turned on"}
```

## Project Structure

- `main.py`: Main application entry point (WiFi connection and IR initialization)
- `http.py`: HTTP web server and REST API implementation
- `config.json`: Configuration file (create this)
- `ir_driver.py`: Low-level IR signal transmission
- `models/nibe.py`: Nibe heat pump IR protocol implementation
- `utils.py`: Utility functions for bit manipulation
- `blink.py`: Simple LED blink test program

## IR Code Origin

The IR protocol implementation is a conversion from the Arduino library [arduino-heatpumpir](https://github.com/ToniA/arduino-heatpumpir) by ToniA, adapted for MicroPython and the Raspberry Pi Pico.

## License

This project is licensed under the GNU General Public License v2.0 (GPL-2.0).

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Disclaimer

This software is provided as-is without warranty. Use at your own risk. Ensure compliance with your heat pump manufacturer's guidelines and local regulations.