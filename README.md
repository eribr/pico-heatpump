# Pico Heat Pump Controller

A complete IoT solution for controlling Nibe heat pumps remotely using a Raspberry Pi Pico with infrared communication and secure SSH tunneling.

## Project Overview

This project consists of two main components that work together to provide remote control of Nibe brand heat pumps:

## Documentation

### 🏠 [pico/](pico/) - Pico Controller
The core MicroPython application that runs on a Raspberry Pi Pico W. It provides:
- **IR Communication**: Controls Nibe heat pumps using infrared signals
- **Web Server**: REST API with HTTP Basic Authentication
- **Heat Pump Control**: Full control over power, temperature, modes, and fan settings
- **[Pico Controller Documentation](pico/README.md)** - Detailed setup and API reference


### 🌐 [tunnel/](tunnel/) - Remote Access Tunnel
SSH tunneling scripts for secure remote access to the pico controller:
- **Reverse SSH Tunnel**: Connects local pico to remote pi-hub server
- **Automatic Reconnection**: Handles network interruptions with exponential backoff
- **Systemd Integration**: Can run as a background service
- **[Tunnel Documentation](tunnel/README.md)** - Remote access setup and configuration

## Quick Start

### 1. Set up the Pico Controller
```bash
cd pico/
# Configure WiFi and authentication in config.json
# Upload code to Raspberry Pi Pico W
```

### 2. Set up Remote Access
```bash
cd tunnel/
# Configure tunnel settings in config.sh
# Run tunnel.sh on pi-satellite
```

### 3. Access Remotely
```
http://your-pi-hub:33333/api/status
```

## Requirements

### Hardware
- Raspberry Pi Pico W (or compatible MicroPython board)
- IR LED connected to GPIO pin
- Nibe brand heat pump with IR remote

### Software
- MicroPython firmware on Pico
- Linux system for tunnel scripts (Raspberry Pi recommended)
- SSH server for remote access

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
