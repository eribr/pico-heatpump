#!/bin/bash

# SSH Tunnel Script for Pico Heat Pump
# Runs on pi-satellite to create a reverse tunnel to pi-hub
# Traffic: pi-hub:33333 -> pi-satellite -> pico:80

# Load configuration from key=value file
load_config() {
    local config_file="$1"

    if [[ ! -f "$config_file" ]]; then
        echo "Error: Configuration file not found: $config_file"
        echo "Please create config.sh in the same directory as this script."
        exit 1
    fi

    # Read config file line by line
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue

        # Remove leading/trailing whitespace
        key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        # Expand environment variables in value (like $HOME)
        value=$(eval echo "$value")

        # Set the variable, but allow environment override
        if [[ -z "${!key}" ]]; then
            export "$key=$value"
        fi
    done < "$config_file"
}

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.sh"
load_config "$CONFIG_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_requirements() {
    if ! command -v ssh &> /dev/null; then
        error "SSH is not installed. Please install openssh-client."
    fi

    SSH_KEY_OPT=""

    log "Prerequisites check passed"
}

# Calculate exponential backoff with maximum of 1 hour
calculate_backoff() {
    local failure_count=$1
    local base_delay=$BASE_RETRY_DELAY
    local max_delay=$MAX_RETRY_DELAY
    local delay=$((base_delay * (2 ** (failure_count - 1))))
    
    # Cap at max_delay
    if [[ $delay -gt $max_delay ]]; then
        delay=$max_delay
    fi
    
    echo $delay
}

# Format seconds to human-readable format
format_duration() {
    local seconds=$1
    if [[ $seconds -ge 3600 ]]; then
        echo "$((seconds / 3600))h $((( seconds % 3600 ) / 60))m"
    elif [[ $seconds -ge 60 ]]; then
        echo "$((seconds / 60))m $((seconds % 60))s"
    else
        echo "${seconds}s"
    fi
}

# Establish the tunnel
establish_tunnel() {
    info "Creating reverse SSH tunnel..."
    info "Configuration:"
    info "  Hub: $HUB_USER@$HUB_HOST:$HUB_PORT"
    info "  Hub forward port: $HUB_FORWARD_PORT"
    info "  Pico endpoint: $PICO_HOST:$PICO_PORT"

    # SSH reverse port forwarding with keep-alive options
    ssh \
        -N \
        -R "$HUB_FORWARD_PORT:$PICO_HOST:$PICO_PORT" \
        -p "$HUB_PORT" \
        -o StrictHostKeyChecking=accept-new \
        -o ServerAliveInterval=60 \
        -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes \
        $SSH_KEY_OPT \
        "$HUB_USER@$HUB_HOST"

    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        info "Tunnel closed normally"
    else
        error "SSH tunnel failed with exit code $exit_code"
    fi
}

# Main loop with exponential backoff
main() {
    info "Pico Heat Pump SSH Tunnel started"
    info "Logs will be written to: $LOG_FILE"

    check_requirements

    local failure_count=0

    # Infinite loop to maintain connection
    while true; do
        establish_tunnel
        
        ((failure_count++))
        
        local backoff_delay=$(calculate_backoff $failure_count)
        local formatted_delay=$(format_duration $backoff_delay)
        
        if [[ $failure_count -lt 3 ]]; then
            warning "Tunnel disconnected (attempt $failure_count). Reconnecting in $formatted_delay..."
        elif [[ $failure_count -lt $MAX_CONSECUTIVE_FAILURES ]]; then
            warning "Tunnel disconnected (attempt $failure_count). Hub may be unreachable. Reconnecting in $formatted_delay..."
        else
            warning "Tunnel disconnected (attempt $failure_count). Extended backoff - hub appears to be down. Next retry in $formatted_delay..."
        fi
        
        sleep "$backoff_delay"
    done
}

# Trap signals for graceful shutdown
trap 'info "Tunnel script terminated by user"; exit 0' SIGINT SIGTERM

# Run main function
main
