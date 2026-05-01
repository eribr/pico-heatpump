# Nibe Heatpump Web Interface

A lightweight PHP-based web interface to control a Nibe Heatpump via a REST API. This interface acts as a frontend for the `nibe_server.py` controller, communicating through a secure SSH tunnel.

## Architecture

1.  **Raspberry Pi**: Runs `pigpiod` and the Python REST API (`nibe_server.py`) on port `5000`.
2.  **Web Server**: Runs this PHP interface.
3.  **SSH Tunnel**: Connects the Web Server's local port `30000` to the Raspberry Pi's port `5000`.

## Installation

Set up apache
```
sudo apt update && sudo apt install -y apache2 php libapache2-mod-php php-curl php-json
sudo systemctl restart apache2
sudo chown -R erik:www-data /var/www/html
sudo chmod -R 775 /var/www/html

```

### 1. Requirements
*   PHP 7.4 or higher
*   `php-curl` extension
*   A running SSH tunnel to the Raspberry Pi

### 2. Configuration
Create a `config.json` file **outside** of your web server's public HTML root (e.g., in `/home/erik/pico-heatpump/website/`) to keep your credentials secure.

Example `config.json`:
```json
{
    "api_password": "your_secure_password",
    "api_base_url": "http://localhost:30000/api"
}
```
