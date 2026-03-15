import network
import socket
import time
import ujson
import ubinascii
import ure
from models.nibe import NibeHeatpumpIR
from ir_driver import IRDriver
from http import run_server

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return ujson.load(f)
    except Exception as e:
        print("Error loading config.json:", e)
        return None

def print_network_info(wlan):
    """Print detailed network information"""
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