# Setting up Cloudflare Tunnel (cloudflared)
This guide explains how to expose your Nibe Heatpump web interface to the internet securely without opening any ports in your home router. By using a Cloudflare Tunnel, your Raspberry Pi establishes an outbound connection to Cloudflare, and all traffic is routed through this encrypted tunnel.
Prerequisites

* A Cloudflare account with a domain pointed to Cloudflare's nameservers.

* A Raspberry Pi running Apache with your heatpump.php script.

## 1. Install cloudflared on Raspberry Pi

First, download and install the Cloudflare Tunnel client.
```bash

# For 32-bit Raspberry Pi OS (older models/standard)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm.deb

# For 64-bit Raspberry Pi OS (Pi 4 or Pi 5 running 64-bit)
# curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb

sudo dpkg -i cloudflared.deb
```

## 2. Authenticate the Client

Link your Raspberry Pi to your Cloudflare account.
```bash
cloudflared tunnel login
```
1. Click the link provided in the terminal.
2. Log in to your Cloudflare account.
3. Select your domain to authorize the connection.

## 3. Create a Tunnel

Create a named tunnel (e.g., nibe-tunnel).
```bash

cloudflared tunnel create nibe-tunnel
```

Note: Copy the Tunnel ID (the UUID) provided in the output. You will need it for the configuration file.

## 4. Configure the Tunnel

Create a configuration directory and file.
```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

Paste the following content (replace placeholders with your actual Tunnel ID and username):

```yaml

tunnel: <YOUR-TUNNEL-UUID>
credentials-file: /home/<user>/.cloudflared/<YOUR-TUNNEL-UUID>.json

ingress:
  - hostname: <full fqdn>
    service: https://localhost
    originRequest:
      noTLSVerify: true  # Necessary because we use a self-signed certificate locally
  - service: http_status:404
```

## 5. Route the DNS

Point your subdomain to the tunnel.
```bash
cloudflared tunnel route dns nibe-tunnel <full fqdn>
```

This replaces any existing A-records for the name noted in the fqdn in your Cloudflare DNS panel with a CNAME pointing to the tunnel.

## 6. Run as a System Service

To ensure the tunnel starts automatically when the Raspberry Pi boots, install it as a systemd service.
```bash

# Install the service
sudo cloudflared --config /home/<user>/.cloudflared/config.yml service install

# Start the service
sudo systemctl start cloudflared

# Enable it to start on boot
sudo systemctl enable cloudflared
```

## Security Benefits

* No Open Ports: You can close port 80 and 443 in your router's Port Forwarding settings. The router remains invisible to scanners.

* Encrypted Traffic: The connection is encrypted from the visitor's browser to Cloudflare, and from Cloudflare to your Pi.

* DDoS Protection: Cloudflare's edge network protects your home network from malicious traffic.

## Troubleshooting

Check the logs if the tunnel isn't working:
```bash
journalctl -u cloudflared -f
```

Make sure your Apache server is running locally on port 443 with the self-signed certificate before starting the tunnel.