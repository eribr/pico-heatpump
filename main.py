# Standard library imports (with fallbacks)
try:
    import socket
    SOCKET_AVAILABLE = True
except ImportError:
    try:
        import usocket as socket
        SOCKET_AVAILABLE = True
    except ImportError:
        socket = None
        SOCKET_AVAILABLE = False

import time

# Check if we're running on MicroPython
try:
    import sys
    MICROPYTHON = sys.implementation.name == 'micropython'
except:
    MICROPYTHON = False

# MicroPython-specific imports
if MICROPYTHON:
    try:
        import network
        import ujson
        import ubinascii
        import ure
        FULL_MICROPYTHON = True
    except ImportError:
        FULL_MICROPYTHON = False
        # Try to import what we can
        try:
            import network
        except:
            network = None
        try:
            import ujson
        except:
            import json as ujson
        try:
            import ubinascii
        except:
            import base64 as ubinascii
        try:
            import ure
        except:
            ure = None
else:
    # Running on regular Python - simulate or skip MicroPython features
    MICROPYTHON = False
    FULL_MICROPYTHON = False
    network = None
    import json as ujson
    import base64 as ubinascii
    ure = None

from models.nibe import NibeHeatpumpIR
from ir_driver import IRDriver
from http import run_server

def load_config():
    """Load configuration from config.json"""
    if not MICROPYTHON:
        print("Development mode: Using mock configuration")
        return {
            "wifi": {"ssid": "mock_ssid", "password": "mock_password"},
            "auth": {"username": "admin", "password": "password123"},
            "server": {"port": 80},
            "hardware": {"ir_pin": "LED"}
        }

    try:
        with open('config.json', 'r') as f:
            return ujson.load(f)
    except Exception as e:
        print("Error loading config.json:", e)
        return None

def print_network_info(wlan):
    """Print detailed network information"""
    if wlan is None:
        print('=' * 40)
        print('Network Information (Mock):')
        print('IP Address: 192.168.1.100')
        print('Subnet Mask: 255.255.255.0')
        print('Gateway: 192.168.1.1')
        print('DNS Server: 8.8.8.8')
        print('=' * 40)
        print('Server will be accessible at: http://192.168.1.100')
        return

    ip_info = wlan.ifconfig()
    print('=' * 40)
    print('Network Information:')
    print(f'IP Address: {ip_info[0]}')
    print(f'Subnet Mask: {ip_info[1]}')
    print(f'Gateway: {ip_info[2]}')
    print(f'DNS Server: {ip_info[3]}')
    print('=' * 40)
    print(f'Server will be accessible at: http://{ip_info[0]}')

def connect_wifi(ssid, password):
    """Connect to WiFi network"""
    if not MICROPYTHON or network is None:
        print('Network module not available - simulating WiFi connection...')
        time.sleep(1)
        print('Mock WiFi connection established')
        print_network_info(None)  # Pass None for mock
        return True

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)

        # Wait for connection with timeout
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print('.', end='')

        if wlan.isconnected():
            print('\nConnected to WiFi')
            print_network_info(wlan)
            return True
        else:
            print('\nFailed to connect to WiFi')
            return False

    print('Already connected to WiFi')
    print_network_info(wlan)
    return True

def main():
    print('Pico Heat Pump Controller')

    if not MICROPYTHON:
        print('Running in development mode on regular Python')
        print('MicroPython-specific features (IR control, web server) are not available')
        return

    if not SOCKET_AVAILABLE:
        print('Error: Socket module not available. Cannot start web server.')
        return

    # Load configuration
    config = load_config()
    if not config:
        print('Failed to load configuration')
        return

    # Connect to WiFi
    if not connect_wifi(config['wifi']['ssid'], config['wifi']['password']):
        print('WiFi connection failed')
        return

    # Initialize IR components
    ir_driver = IRDriver(config['hardware']['ir_pin'])
    ir_driver.set_frequency(38)
    nibe_ir = NibeHeatpumpIR()

    # Start web server
    run_server(config, ir_driver, nibe_ir)

if __name__ == "__main__":
    main()