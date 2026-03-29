# SSH Tunnel Configuration

This directory contains the SSH tunnel script for connecting the pico heat pump to the pi-hub server.

## Architecture

```
pi-satellite (local pico network)
    |
    | ssh -R 33333:localhost:80
    |
pi-hub (remote)
    |
Client connects to pi-hub:33333 -> forwarded to pico:80
```

## Setup

### On pi-satellite (at the pico location):

1. **Copy the tunnel files**
   ```bash
   cp tunnel.sh config.sh /home/pi/
   chmod +x /home/pi/tunnel.sh
   ```

2. **Edit configuration** (optional - defaults should work)
   ```bash
   nano /home/pi/config.sh
   ```

3. **Configure SSH key authentication (optional but recommended)**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
   ssh-copy-id -p 20022 pi@bergfur.dyndns.org
   ```

4. **Set up as a systemd service** (optional - for auto-restart)
   
   Create `/etc/systemd/system/pico-tunnel.service`:
   ```ini
   [Unit]
   Description=Pico Heat Pump SSH Tunnel
   After=network-online.target
   Wants=network-online.target
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi
   ExecStart=/home/pi/tunnel.sh
   Restart=always
   RestartSec=10
   Environment="HUB_HOST=bergfur.dyndns.org"
   Environment="HUB_USER=pi"
   Environment="PICO_HOST=localhost"
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Then enable and start:
   ```bash
   sudo systemctl enable pico-tunnel
   sudo systemctl start pico-tunnel
   ```

### On pi-hub:

1. **Ensure SSH server is running** with remote port forwarding enabled
   
   In `/etc/ssh/sshd_config`:
   ```
   GatewayPorts yes
   ```
   
   Restart SSH: `sudo systemctl restart ssh`

2. **Monitor tunnel status**
   ```bash
   ss -nltp | grep 33333
   ```

## Configuration

Configuration is stored in `config.sh` (a simple key=value file that is **not committed to git**):

```bash
# SSH Tunnel Configuration for Pico Heat Pump
# Lines starting with # are comments and are ignored
# Values can be overridden with environment variables

# Hub (pi-hub) configuration
HUB_HOST=bergfur.dyndns.org
HUB_PORT=20022
HUB_USER=pi
HUB_FORWARD_PORT=33333

# Pico endpoint configuration
PICO_HOST=localhost
PICO_PORT=80

# Local configuration
LOG_FILE=/tmp/pico-tunnel.log
SSH_KEY=$HOME/.ssh/id_rsa

# Retry configuration
MAX_CONSECUTIVE_FAILURES=10
BASE_RETRY_DELAY=10
MAX_RETRY_DELAY=3600
```

| Variable | Default | Description |
|----------|---------|-------------|
| `HUB_HOST` | `bergfur.dyndns.org` | Pi-hub hostname/IP |
| `HUB_PORT` | `20022` | SSH port on pi-hub |
| `HUB_USER` | `pi` | SSH user on pi-hub |
| `HUB_FORWARD_PORT` | `33333` | Port on pi-hub to expose |
| `PICO_HOST` | `localhost` | Pico hostname/IP (local network) |
| `PICO_PORT` | `80` | Pico HTTP server port |
| `SSH_KEY` | `$HOME/.ssh/id_rsa` | SSH private key path |
| `LOG_FILE` | `/tmp/pico-tunnel.log` | Log file location |
| `MAX_CONSECUTIVE_FAILURES` | `10` | Threshold for extended backoff messages |
| `BASE_RETRY_DELAY` | `10` | Base delay in seconds for exponential backoff |
| `MAX_RETRY_DELAY` | `3600` | Maximum retry delay (1 hour) |

### Editing Configuration

**Option 1: Edit config.sh directly**
```bash
nano config.sh
```

**Option 2: Override with environment variables**
```bash
export HUB_HOST=my-custom-host.com
export HUB_PORT=2222
./tunnel.sh
```

**Option 3: Use systemd environment variables**
```ini
[Service]
Environment="HUB_HOST=my-custom-host.com"
Environment="HUB_PORT=2222"
```

## Usage

**Start the tunnel:**
```bash
./tunnel.sh
```

**Run in background (with nohup):**
```bash
nohup ./tunnel.sh > /tmp/pico-tunnel.log 2>&1 &
```

**Monitor logs:**
```bash
tail -f /tmp/pico-tunnel.log
```

**Stop the tunnel:**
```bash
killall tunnel.sh
```
or
```bash
pgrep -f "tunnel.sh" | xargs kill
```

## Testing

1. **From pi-satellite, test local access:**
   ```bash
   curl http://localhost:80
   ```

2. **From pi-hub, test forwarded port:**
   ```bash
   curl http://localhost:33333
   ```

3. **From remote client:**
   ```bash
   curl http://bergfur.dyndns.org:33333
   ```

## Troubleshooting

### Connection refused
- Verify pi-hub SSH server is running and configured with `GatewayPorts yes`
- Check firewall rules on both machines
- Verify the SSH credentials are correct

### Tunnel disconnects frequently
- Check network stability on pi-satellite
- Increase `ServerAliveInterval` in the script if needed
- Use systemd service with `Restart=always` for automatic reconnection

### Permission denied (publickey)
- Generate SSH key pair: `ssh-keygen -t rsa -b 4096`
- Copy to pi-hub: `ssh-copy-id -p 20022 pi@bergfur.dyndns.org`
- Or set password-based authentication

### Cannot bind to port 33333
- Port might already be in use: `ss -nltp | grep 33333`
- Kill existing process or use different port
- Note: Ports below 1024 require root privileges

## Security Considerations

- ✅ Use SSH key authentication instead of passwords
- ✅ Restrict SSH access to known IPs where possible
- ✅ Monitor tunnel logs for unexpected connections
- ✅ Use a firewall to restrict access to port 33333 on pi-hub
- ✅ Consider using a VPN for additional security
