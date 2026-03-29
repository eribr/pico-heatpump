# Heatpump Website

Complete automation for setting up a secure Apache web server with HTML interface to control your Nibe heat pump through the Pico REST API.

## Overview

This folder contains everything needed to set up a professional web interface for controlling your heat pump:

✅ **HTML Interface** - Beautiful, responsive design  
✅ **PHP API Bridge** - Secure connection to Pico REST API  
✅ **HTTP Basic Authentication** - Username/password protected access  
✅ **Self-signed SSL Certificate** - Auto-generated HTTPS  
✅ **Secure Credentials** - Pico API credentials stored outside web root  
✅ **Apache Configuration** - Ready-to-use virtual host setup  
✅ **Security Headers** - XSS, Clickjacking, MIME-type protection  

## Folder Structure

```
website/
├── html/                   # Website files
│   ├── index.html          # Main HTML interface
│   ├── css/
│   │   └── style.css       # Styling
│   └── js/
│       └── heatpump.js     # Frontend logic
├── setup-website.py        # Python setup script (cross-platform)
└── README.md              # This file
```

## Quick Start

### 1. Set Environment Variables (optional)

```bash
export DOMAIN="my.hidden.backend.com"
export PICO_HOST="192.168.1.100"          # Pico IP or hostname
export PICO_PORT="80"                     # Pico API port
export PICO_USERNAME="admin"              # Pico API username
export PICO_PASSWORD="password123"        # Pico API password
```

### 2. Run Setup

On **Linux/Raspberry Pi**:

```bash
cd website

# Run Python setup (you'll be prompted for credentials)
sudo python3 setup-website.py
```

During setup, you will be prompted for:
- **Website username** (default: `admin`)
- **Website password** (required, must be confirmed)
- Pico API connection details (if not set via environment variables)

### 3. Access Website

Open browser:
```
https://my.hidden.backend.com/
```

**Note:** You'll see an SSL certificate warning (self-signed). Click "Accept risk" or "Proceed anyway" to continue.

## What Gets Set Up

**System Configuration:**
- ✅ Apache web server with SSL/TLS
- ✅ PHP runtime environment
- ✅ Self-signed certificate (`/etc/ssl/heatpump/`)
- ✅ Secure config file (`/etc/heatpump/pico-api.conf.php`)
- ✅ Web root at `/var/www/heatpump/`

**Web Interface Features:**
- Power control (On/Off)
- Operating modes (Auto, Heat, Cool, Dry, Fan)
- Temperature setting (10-32°C with +/- buttons)
- Fan speed (Silent, Levels 2-4, Auto)
- Vertical swing (7 positions)
- Live status display (auto-refreshes every 30 seconds)
- Responsive design (works on desktop, tablet, mobile)

**API Bridge:**
- PHP bridge connects frontend to Pico API
- Transparent credential handling (never exposed to browser)
- Automatic request routing and response formatting
- Error handling and logging

**Authentication:**
- ✅ HTTP Basic Authentication (username/password)
- ✅ `.htpasswd` file for user management (`/etc/heatpump/.htpasswd`)
- ✅ Credentials required for all website access
- ✅ Browser login prompt for easy access

## Authentication

### How It Works

The website uses **HTTP Basic Authentication** - when you access the site, the browser shows a login dialog. You must enter the username and password set during setup.

### Changing Credentials

To change the website username and password:

**Method 1: Re-run setup**
```bash
sudo python3 setup-website.py
# You'll be prompted for new credentials
```

**Method 2: Update .htpasswd directly**
```bash
# Add new user or update existing
sudo htpasswd /etc/heatpump/.htpasswd username

# View all users
sudo cat /etc/heatpump/.htpasswd
```

**Method 3: Using htpasswd (bcrypt)**
```bash
# Generate new password
sudo htpasswd -B /etc/heatpump/.htpasswd myuser
# Enter password when prompted
```

### Disabling Authentication (NOT recommended)

If you want to disable authentication (only for internal networks):

1. Edit Apache config:
```bash
sudo nano /etc/apache2/sites-available/heatpump.conf
```

2. Find the `<Directory>` section and remove or comment these lines:
```apache
# AuthType Basic
# AuthName "Heatpump Control"
# AuthUserFile /etc/heatpump/.htpasswd
# Require valid-user
```

3. Restart Apache:
```bash
sudo systemctl restart apache2
```

**⚠️ Warning:** Without authentication, anyone with network access can control your heat pump!

## Security

### Credential Protection
- ✅ Website access controlled with HTTP Basic Auth (username/password)
- ✅ Pico API credentials stored in `/etc/heatpump/` (outside web root)
- ✅ Config file only readable by `www-data` user (640 permissions)
- ✅ Credentials never exposed in HTML, CSS, or JavaScript
- ✅ Frontend only calls local PHP bridge endpoint

### HTTPS/SSL
- Self-signed certificate auto-generated
- TLS 1.2+ enforced
- HTTP automatically redirects to HTTPS
- HSTS header forces secure connections

### Security Headers
```
X-Frame-Options: DENY                          # Prevent clickjacking
X-Content-Type-Options: nosniff                # Prevent MIME-type sniffing
X-XSS-Protection: 1; mode=block                # XSS protection
Strict-Transport-Security: max-age=31536000    # Force HTTPS
```

## How It Works

### Request Flow

```
Browser JavaScript (HTTPS)
    ↓ fetch('/heatpump-api.php/power/on')
Apache + PHP Bridge (runs as www-data)
    ↓ Loads Pico credentials from /etc/heatpump/
    ↓ Constructs authenticated request
Internal Network (HTTP + Basic Auth)
    ↓ Connects to Pico API
Pico Controller
    ↓ Sends IR command
Nibe Heat Pump
```

### Data Security

1. **Browser → Server**: HTTPS encrypted, no credentials
2. **Server-side**: Credentials loaded from secure file
3. **Server → Pico**: Internal network, authenticated with stored credentials
4. **Response**: Returned to browser as JSON, no sensitive data

## Updating Pico Credentials

If your Pico API credentials change:

```bash
# Method 1: Edit config file directly
sudo nano /etc/heatpump/pico-api.conf.php

# Method 2: Re-run setup with new environment variables
export PICO_USERNAME="newuser"
export PICO_PASSWORD="newpass"
sudo python3 setup-website.py
```

## Troubleshooting

### "Connection refused" or "Connection timeout"

Check if Pico is reachable:
```bash
curl -u admin:password http://192.168.1.100:80/api/status
```

Check PHP logs:
```bash
sudo tail -f /var/log/heatpump/php-error.log
```

Edit config to match your Pico:
```bash
sudo nano /etc/heatpump/pico-api.conf.php
```

### SSL Certificate Warnings

**Expected behavior** - Self-signed certificates always show warnings in browsers.

To regenerate certificate:
```bash
sudo rm /etc/ssl/heatpump/*.pem
sudo python3 setup-website.py
```

### Authentication Issues

**"401 Unauthorized" or login prompt not appearing:**
- Verify `.htpasswd` file exists: `sudo ls -la /etc/heatpump/.htpasswd`
- Check Apache has read permissions: `sudo chown www-data:www-data /etc/heatpump/.htpasswd`
- Verify Apache config has auth directives: `sudo apache2ctl configtest`

**Forgot website password:**
```bash
# Reset password for existing user
sudo htpasswd /etc/heatpump/.htpasswd admin
# Enter new password when prompted

# Or re-run full setup
sudo python3 setup-website.py
```

**Can't login even with correct password:**
- Check browser cache (try private/incognito window)
- Restart Apache: `sudo systemctl restart apache2`
- Check htpasswd file format: `sudo cat /etc/heatpump/.htpasswd`

### "Access denied" errors

Fix file permissions:
```bash
sudo chown -R www-data:www-data /var/www/heatpump/
sudo chmod -R 755 /var/www/heatpump/
sudo chown -R root:www-data /etc/heatpump/
sudo chmod 750 /etc/heatpump/
sudo chmod 640 /etc/heatpump/.htpasswd
sudo chmod 640 /etc/heatpump/pico-api.conf.php
```

### Apache won't start

Verify Apache configuration:
```bash
sudo apache2ctl configtest

# If error, check heatpump config
sudo cat /etc/apache2/sites-available/heatpump.conf
```

## Logs and Monitoring

Monitor website activity:

```bash
# Apache access log
sudo tail -f /var/log/apache2/heatpump-access.log

# Apache error log
sudo tail -f /var/log/apache2/heatpump-error.log

# PHP errors
sudo tail -f /var/log/heatpump/php-error.log

# Check Apache status
sudo systemctl status apache2
```

## API Endpoints

You can also interact with the API directly (via the PHP bridge) using curl:

```bash
# Get status (with basic auth)
curl -k -u username:password https://my.hidden.backend.com/heatpump-api.php/status

# Power control (with basic auth)
curl -k -u username:password -X PUT https://my.hidden.backend.com/heatpump-api.php/power/on
curl -k -u username:password -X PUT https://my.hidden.backend.com/heatpump-api.php/power/off

# Set temperature to 22°C (with basic auth)
curl -k -u username:password -X PUT https://my.hidden.backend.com/heatpump-api.php/temp/22

# Set mode to cool (with basic auth)
curl -k -u username:password -X PUT https://my.hidden.backend.com/heatpump-api.php/mode/cool

# Set fan speed (with basic auth)
curl -k -u username:password -X PUT https://my.hidden.backend.com/heatpump-api.php/fan/silent
```

**Note:** 
- Replace `username:password` with your website credentials
- Use `-k` flag to accept self-signed certificate
- `-u` flag provides HTTP Basic Auth credentials

## Uninstall

To remove the website setup:

```bash
# Disable Apache site
sudo a2dissite heatpump
sudo rm /etc/apache2/sites-available/heatpump.conf

# Remove web files
sudo rm -rf /var/www/heatpump/

# Remove configuration
sudo rm -rf /etc/heatpump/

# Remove certificates
sudo rm -rf /etc/ssl/heatpump/

# Restart Apache
sudo systemctl restart apache2
```

## Advanced Configuration

### Change Port

Edit Apache config:
```bash
sudo nano /etc/apache2/sites-available/heatpump.conf
# Change: <VirtualHost *:443>
# To: <VirtualHost *:8443>
```

Then restart Apache and use `https://domain:8443/`

### Auto-start on Boot

Website automatically starts with Apache:
```bash
# Enable Apache on boot
sudo systemctl enable apache2

# Check status
sudo systemctl is-enabled apache2
```

### Multiple Instances

To run multiple domain/server combinations:

```bash
# Instance 1
export DOMAIN="domain1.com" PICO_HOST="192.168.1.100"
sudo python3 setup-website.py

# Instance 2 (creates separate Apache config)
export DOMAIN="domain2.com" PICO_HOST="192.168.1.101"
sudo python3 setup-website.py
```

## Performance

- **Status Refresh**: Every 30 seconds (configurable in `js/heatpump.js`)
- **Connection Timeout**: 10 seconds
- **Page Load**: ~1-2 MB (first load), ~100KB (cached)

To change refresh interval:
```javascript
# Edit html/js/heatpump.js
# Line: setInterval(refreshStatus, 30000);
# Change 30000 to desired interval (milliseconds)
```

## For Detailed Information

See [WEBSITE-SETUP.md](WEBSITE-SETUP.md) for:
- Complete setup instructions
- Comprehensive troubleshooting
- Security architecture details
- All available API endpoints
- Monitoring and logging
- Advanced configuration
- Performance tuning

## Cloudflare Integration

This website works perfectly with the Cloudflare proxy setup in the [../cloudflare/](../cloudflare/) folder.

**Setup flow:**
1. Set up this website (you are here)
2. Set up Cloudflare proxy to expose website to internet
3. Access: `https://hidden.example.com/` (via Cloudflare)
4. Or locally: `https://my.hidden.backend.com/` (direct)

See [../cloudflare/README.md](../cloudflare/README.md) for proxy setup.

## License

This project is part of the Pico Heat Pump Controller project.
