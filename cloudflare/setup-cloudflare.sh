#!/bin/bash

# Cloudflare DNS Proxy Setup Script
# Sets up a free Cloudflare proxy for hiding internal server address
# Usage: ./setup-cloudflare.sh

set -e

# Configuration
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-}"
CLOUDFLARE_ZONE_ID="${CLOUDFLARE_ZONE_ID:-}"
CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-}"

DOMAIN_NAME="hidden.example.com"
ORIGIN_HOST="my.hidden.backend.com"
ORIGIN_PORT="443"
ZONE_NAME="example.com"  # Your domain zone in Cloudflare

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validate requirements
validate_requirements() {
    echo -e "${YELLOW}Validating requirements...${NC}"
    
    if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
        echo -e "${RED}Error: CLOUDFLARE_API_TOKEN environment variable is not set${NC}"
        echo "Get your API token from: https://dash.cloudflare.com/profile/api-tokens"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}Error: curl is required but not installed${NC}"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq is required but not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Requirements validated${NC}"
}

# Get Cloudflare Zone ID
get_zone_id() {
    echo -e "${YELLOW}Getting Cloudflare Zone ID for ${ZONE_NAME}...${NC}"
    
    RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=${ZONE_NAME}" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json")
    
    CLOUDFLARE_ZONE_ID=$(echo $RESPONSE | jq -r '.result[0].id')
    
    if [ "$CLOUDFLARE_ZONE_ID" = "null" ] || [ -z "$CLOUDFLARE_ZONE_ID" ]; then
        echo -e "${RED}Error: Could not find zone for ${ZONE_NAME}${NC}"
        echo "Make sure your domain is added to Cloudflare"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Zone ID: $CLOUDFLARE_ZONE_ID${NC}"
}

# Create or update DNS record with proxying enabled (orange cloud)
setup_dns_record() {
    echo -e "${YELLOW}Setting up DNS record: $DOMAIN_NAME -> $ORIGIN_HOST:$ORIGIN_PORT (proxied)${NC}"
    
    # Check if record exists
    EXISTING=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/dns_records?name=${DOMAIN_NAME}" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json")
    
    RECORD_ID=$(echo $EXISTING | jq -r '.result[0].id')
    
    # Prepare DNS record data
    DNS_DATA=$(cat <<EOF
{
  "type": "CNAME",
  "name": "$DOMAIN_NAME",
  "content": "$ORIGIN_HOST",
  "ttl": 3600,
  "proxied": true,
  "comment": "CloudFlare proxy hiding internal server"
}
EOF
)
    
    if [ "$RECORD_ID" != "null" ] && [ ! -z "$RECORD_ID" ]; then
        # Update existing record
        echo -e "${YELLOW}Updating existing DNS record...${NC}"
        RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/dns_records/${RECORD_ID}" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$DNS_DATA")
    else
        # Create new record
        echo -e "${YELLOW}Creating new DNS record...${NC}"
        RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/dns_records" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$DNS_DATA")
    fi
    
    SUCCESS=$(echo $RESPONSE | jq -r '.success')
    
    if [ "$SUCCESS" = "true" ]; then
        RECORD_ID=$(echo $RESPONSE | jq -r '.result.id')
        echo -e "${GREEN}✓ DNS record configured successfully (ID: $RECORD_ID)${NC}"
    else
        echo -e "${RED}Error setting up DNS record:${NC}"
        echo $RESPONSE | jq '.'
        exit 1
    fi
}

# Configure SSL/TLS settings for enhanced security
setup_ssl_tls() {
    echo -e "${YELLOW}Configuring SSL/TLS settings...${NC}"
    
    # Enable "Flexible SSL" or "Full" SSL mode (requires valid cert on origin)
    SSL_CONFIG=$(cat <<EOF
{
  "value": "full"
}
EOF
)
    
    RESPONSE=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/settings/ssl" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$SSL_CONFIG")
    
    if echo $RESPONSE | jq -e '.success' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ SSL/TLS configured to Full mode${NC}"
    else
        echo -e "${YELLOW}⚠ Could not configure SSL/TLS (may already be set or restricted on free plan)${NC}"
    fi
}

# Add security headers via Cloudflare
setup_security_headers() {
    echo -e "${YELLOW}Adding security headers...${NC}"
    
    # Note: Headers are typically set at the origin server level
    # This is informational for best practices
    echo -e "${GREEN}✓ Recommend these headers on origin server:${NC}"
    echo "  X-Frame-Options: DENY"
    echo "  X-Content-Type-Options: nosniff"
    echo "  X-XSS-Protection: 1; mode=block"
    echo "  Strict-Transport-Security: max-age=31536000; includeSubDomains"
}

# Display final information
display_summary() {
    echo ""
    echo -e "${GREEN}=== Cloudflare Proxy Setup Complete ===${NC}"
    echo ""
    echo "Configuration Summary:"
    echo "  Public DNS:       $DOMAIN_NAME"
    echo "  Origin Server:    $ORIGIN_HOST:$ORIGIN_PORT"
    echo "  Proxying:         Enabled (Orange Cloud)"
    echo "  Zone ID:          $CLOUDFLARE_ZONE_ID"
    echo "  SSL/TLS Mode:     Full"
    echo ""
    echo -e "${YELLOW}Important:${NC}"
    echo "  1. Your internal IP ($ORIGIN_HOST) is now hidden from public"
    echo "  2. All traffic is proxied through Cloudflare"
    echo "  3. DNS queries will return Cloudflare IP addresses"
    echo "  4. Ensure your origin server has a valid SSL certificate"
    echo "  5. Configure firewall rules on origin to only accept Cloudflare IPs"
    echo ""
    echo "Next steps:"
    echo "  • Update your origin server firewall to only allow Cloudflare IP ranges"
    echo "  • See: https://www.cloudflare.com/ips/"
    echo "  • Test: curl -H 'Host: $DOMAIN_NAME' https://$DOMAIN_NAME"
    echo ""
}

# Main execution
main() {
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║   Cloudflare Free Proxy Setup                            ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    validate_requirements
    get_zone_id
    setup_dns_record
    setup_ssl_tls
    setup_security_headers
    display_summary
}

main "$@"
