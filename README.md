# Pico Heat Pump Controller

A complete IoT solution for controlling Nibe heat pumps remotely using a Raspberry Pi Pico with infrared communication and secure SSH tunneling.

## Project Overview

This project consists of two main components that work together to provide remote control of Nibe brand heat pumps:

## Documentation

### 🏠 [raspberrypi/](raspberrypi/) - Raspberry Pi Controller & REST API Server
The core MicroPython application that runs on a Raspberry Pi Pico W. It provides:
- **IR Communication**: Controls Nibe heat pump using infrared signals
- **Web Server**: REST API with HTTP Basic Authentication
- **Heat Pump Control**: Control power, temperature and fan settings
- **[Raspberry pi Controller Documentation](raspberrypi/README.md)** - Detailed setup and API reference

### 🏠 [pico/](pico/) - Pico Controller
*Untested* Does not use my heatpump model
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

### 🌐 [website/](website/) - Heatpump Web Interface
Beautiful HTML interface with PHP API bridge for secure heat pump control:
- **HTML Interface**: Responsive design for desktop, tablet, mobile
- **PHP API Bridge**: Secure bridging between frontend and Pico API
- **Self-signed SSL**: HTTPS encryption with auto-generated certificates
- **Secure Credentials**: Pico API credentials stored outside web root
- **[Website Setup Documentation](website/README.md)** - Complete setup and configuration

### ☁️ [cloudflare/](cloudflare/) - Public HTTPS Proxy
Free Cloudflare proxy automation to securely expose your internal server:
- **DNS Proxy (Orange Cloud)**: Hides your real server IP from the public internet
- **Automatic Setup**: Python script for easy configuration
- **Security**: Never exposes `my.hidden.backend.com:443` - only public proxy domain visible
- **[Cloudflare Setup Documentation](cloudflare/README.md)** - Complete proxy configuration

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

### 3. Set up Heatpump Web Interface
```bash
cd website/
# Option A: Python (recommended)
sudo python3 setup-website.py
# Option B: Bash  
sudo ./setup-website.sh
# Then access: https://my.hidden.backend.com/
```

### 4. Set up Cloudflare Proxy (Optional but Recommended)
```bash
cd cloudflare/
# Copy config.json.example to config.json
# Edit config.json with your Cloudflare API token and Zone ID
# Run: python setup-cloudflare.py
```

### 5. Access Remotely
```
# Public interface (via Cloudflare proxy):
https://hidden.example.com/api/status

# Web interface (local):
https://my.hidden.backend.com/

# Private interface (via SSH tunnel):
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

This project is licensed under the GPL 2 License - see the [LICENSE](LICENSE) file for details.
