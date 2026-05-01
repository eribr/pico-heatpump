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
sudo chown -R erik:www-data /var/www/html
sudo chmod -R 775 /var/www/html
rm /var/www/html/index.html
ln -s /home/erik/pico-heatpump/website/html/index.html /var/www/html
ln -s /home/erik/pico-heatpump/website/html/heatpump.php /var/www/html

# Enable SSL
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
-keyout /etc/ssl/private/apache-selfsigned.key \
-out /etc/ssl/certs/apache-selfsigned.crt
sudo a2enmod ssl

sudo cp /etc/apache2/sites-available/default-ssl.conf /etc/apache2/sites-available/heatpump-ssl.conf
sudo nano /etc/apache2/sites-available/heatpump-ssl.conf
# Change ssl-config to
# SSLCertificateFile    /etc/ssl/certs/apache-selfsigned.crt
# SSLCertificateKeyFile /etc/ssl/private/apache-selfsigned.key

sudo a2ensite heatpump-ssl.conf

# Disable non-ssl
sudo a2enmod rewrite
sudo nano /etc/apache2/sites-available/000-default.conf
#In the VirtualHost:80 block, add
# RewriteEngine On
# RewriteCond %{HTTPS} off
# RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]


# Finally restart to make all config stick
sudo systemctl restart apache2
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
