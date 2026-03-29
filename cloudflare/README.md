# Cloudflare Free Proxy Setup

This folder contains Python automation for setting up a Cloudflare proxy to hide your internal server address (`bergfur.dyndns.org:66443`) behind a public domain (`oland.bergfur.se`).

## Overview

**Why use Cloudflare?**
- Free tier includes DNS proxying (orange cloud)
- Hides your real server IP from the public internet
- DDos protection and security features
- HTTPS support
- No one can directly access your internal address

## Prerequisites

1. **Cloudflare Account**: https://dash.cloudflare.com/
2. **Domain**: Your domain (`bergfur.se`) must be set to use Cloudflare nameservers
3. **Valid SSL Certificate**: Your origin server must have a valid HTTPS certificate on port 66443
4. **API Token**: Generate one at https://dash.cloudflare.com/profile/api-tokens
   - Permissions needed: "Zone / DNS / Edit"

## Getting Your Credentials

1. **Zone ID**: 
   - Log in to https://dash.cloudflare.com/
   - Select your domain
   - Scroll to "API" section in Overview
   - Copy "Zone ID"

2. **API Token**:
   - Go to My Profile → API Tokens
   - Create new token with "Zone / DNS / Edit" scope
   - Copy the token immediately (you won't see it again)

## Setup

## Setup

### 1. Install Python Requirements

```powershell
# Windows
pip install requests

# macOS/Linux
pip3 install requests
```

### 2. Configure Cloudflare Credentials

```bash
# Copy config template
cp config.json.example config.json

# Or Windows:
copy config.json.example config.json
```

Edit `config.json` with your credentials:
```json
{
  "cloudflare": {
    "api_token": "your-api-token-here",
    "zone_id": "your-zone-id-here"
  },
  "proxy": {
    "subdomain": "oland",
    "domain_zone": "bergfur.se",
    "origin": "bergfur.dyndns.org",
    "origin_port": 66443
  }
}
```

### 3. Run Setup

**Windows:**
```powershell
.\setup-cloudflare.bat
# or run directly:
python setup-cloudflare.py
```

**macOS/Linux:**
```bash
python3 setup-cloudflare.py
```

### Prerequisites
- Python 3.6+
- `requests` package (installed via pip)

## What Gets Configured

### DNS Record
- **Type**: CNAME (proxied)
- **Name**: `oland.bergfur.se`
- **Points to**: `bergfur.dyndns.org`
- **Proxied**: YES (Orange Cloud) - This hides your real IP!

### SSL/TLS Configuration
- **Mode**: Full (requires valid cert on origin)
- **Minimum TLS**: 1.2
- **Always HTTPS**: Enabled

### Security Headers (from origin server)
You should also configure these on your origin server:
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## Security: Protecting Your Origin Server

**Important**: Once the proxy is set up, you should firewall your origin server to only accept traffic from Cloudflare IPs.

### Cloudflare IP Ranges
Get the latest list from: https://www.cloudflare.com/ips/

Example iptables rule (Linux):
```bash
# Whitelist Cloudflare IPs and localhost
for ip in $(curl -s https://www.cloudflare.com/ips-v4); do
  iptables -A INPUT -p tcp --dport 66443 -s $ip -j ACCEPT
done

# Whitelist IPv6 if applicable
for ip in $(curl -s https://www.cloudflare.com/ips-v6); do
  ip6tables -A INPUT -p tcp --dport 66443 -s $ip -j ACCEPT
done

# Drop all other traffic to the port
iptables -A INPUT -p tcp --dport 66443 -j DROP
```

### Origin Server HTTPS Certificate

Your origin server **must** have a valid HTTPS certificate for:
- Domain: `bergfur.dyndns.org`
- Port: `66443`

Options:
1. Use Let's Encrypt (free): https://letsencrypt.org/
2. Self-signed certificate (less secure, but works)

## Verification

### Test DNS Resolution
```bash
nslookup oland.bergfur.se
# Should return Cloudflare IPs, NOT your real server IP
```

### Test HTTPS Connection
```bash
# Test the proxy endpoint
curl -v https://oland.bergfur.se/

# You should see Cloudflare's SSL certificate, not your origin cert
```

### Check x-via-cloudflare Header
```bash
curl -I https://oland.bergfur.se/
# Look for: x-via-cloudflare header
```

## Troubleshooting

### DNS not resolving
- Ensure your domain's nameservers are set to Cloudflare
- Wait up to 48 hours for DNS propagation
- Check: `whois bergfur.se`

### SSL Certificate Error
- Verify origin server has valid certificate on port 66443
- Check certificate brand matches `bergfur.dyndns.org`

### Origin Connection Failed
- Verify origin server is accessible: `curl -k https://bergfur.dyndns.org:66443/`
- Check firewall rules allow port 66443
- Verify Cloudflare IP ranges are whitelisted on origin

### API Token Errors
- Ensure token has "Zone / DNS / Edit" permissions
- Check token hasn't expired
- Verify Zone ID is correct

## Disabling/Reverting Setup

Delete the DNS record manually from Cloudflare dashboard or using the API.

## Further Reading

- [Cloudflare DNS Documentation](https://developers.cloudflare.com/dns/)
- [Orange Cloud vs Gray Cloud](https://developers.cloudflare.com/dns/manage-dns-records/reference/proxied-dns-record/)
- [Cloudflare SSL/TLS Modes](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/)
- [Cloudflare API Reference](https://developers.cloudflare.com/api/)

## Notes

- This uses Cloudflare's **free tier** - no credit card required
- Your billing page will remain free as long as you use free features only
- Cloudflare free includes: DNS, proxying, DDoS protection, basic WAF
- Enterprise features (advanced analytics, strict WAF rules) require paid plans
- Python script is cross-platform compatible (Windows, macOS, Linux)
- Batch wrapper (`setup-cloudflare.bat`) automates everything on Windows
