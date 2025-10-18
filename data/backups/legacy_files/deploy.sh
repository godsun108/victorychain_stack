#!/bin/bash

# VictoryChain Trading Bot - 24/7 Deployment Script
# This script sets up the bot for continuous operation with monitoring and recovery

set -e

# Configuration
BOT_USER="trading"
BOT_HOME="/home/$BOT_USER"
BOT_DIR="$BOT_HOME/victorychain_stack"
SERVICE_NAME="victorychain"
LOG_DIR="$BOT_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)"
fi

log "Starting VictoryChain Bot 24/7 deployment..."

# Create trading user if it doesn't exist
if ! id "$BOT_USER" &>/dev/null; then
    log "Creating trading user..."
    useradd -m -s /bin/bash $BOT_USER
    usermod -aG sudo $BOT_USER
fi

# Create necessary directories
log "Creating directory structure..."
mkdir -p $BOT_DIR
mkdir -p $LOG_DIR
mkdir -p $BOT_DIR/backups

# Install system dependencies
log "Installing system dependencies..."
apt update
apt install -y build-essential curl git pkg-config libssl-dev

# Install Rust for the trading user
log "Installing Rust..."
if ! command -v rustc &> /dev/null; then
    sudo -u $BOT_USER curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sudo -u $BOT_USER sh -s -- -y
    sudo -u $BOT_USER source $BOT_HOME/.cargo/env
fi

# Copy bot files
log "Copying bot files..."
cp -r . $BOT_DIR/
chown -R $BOT_USER:$BOT_USER $BOT_DIR

# Build the bot
log "Building the bot in release mode..."
sudo -u $BOT_USER bash -c "cd $BOT_DIR && source ~/.cargo/env && cargo build --release"

# Install systemd service
log "Installing systemd service..."
cp deploy/systemd/victorychain.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Create log rotation configuration
log "Setting up log rotation..."
cat > /etc/logrotate.d/victorychain << EOF
$LOG_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $BOT_USER $BOT_USER
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

# Create monitoring script
log "Creating monitoring script..."
cat > $BOT_DIR/monitor.sh << 'EOF'
#!/bin/bash

# VictoryChain Bot Monitoring Script
LOG_FILE="/home/trading/victorychain_stack/logs/monitor.log"
BOT_SERVICE="victorychain"

log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if bot is running
if ! systemctl is-active --quiet $BOT_SERVICE; then
    log_with_timestamp "ERROR: Bot service is not running. Attempting restart..."
    systemctl restart $BOT_SERVICE
    sleep 10
    
    if systemctl is-active --quiet $BOT_SERVICE; then
        log_with_timestamp "SUCCESS: Bot service restarted successfully"
    else
        log_with_timestamp "CRITICAL: Failed to restart bot service"
        # Send alert (implement your preferred alerting method)
        # curl -X POST "your-webhook-url" -d "VictoryChain Bot failed to restart"
    fi
else
    log_with_timestamp "INFO: Bot service is running normally"
fi

# Check memory usage
MEMORY_USAGE=$(ps -o pid,user,%mem,command -p $(pgrep backend) | tail -1 | awk '{print $3}')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    log_with_timestamp "WARNING: High memory usage detected: ${MEMORY_USAGE}%"
fi

# Check disk space
DISK_USAGE=$(df /home/trading | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    log_with_timestamp "WARNING: High disk usage detected: ${DISK_USAGE}%"
fi

# Check for rate limit warnings in logs
RATE_LIMIT_WARNINGS=$(tail -1000 /home/trading/victorychain_stack/logs/trading.log | grep -c "rate limit" || true)
if [ "$RATE_LIMIT_WARNINGS" -gt 5 ]; then
    log_with_timestamp "WARNING: Multiple rate limit warnings detected: $RATE_LIMIT_WARNINGS"
fi
EOF

chmod +x $BOT_DIR/monitor.sh
chown $BOT_USER:$BOT_USER $BOT_DIR/monitor.sh

# Create cron job for monitoring
log "Setting up monitoring cron job..."
crontab -u $BOT_USER -l 2>/dev/null | { cat; echo "*/5 * * * * $BOT_DIR/monitor.sh"; } | crontab -u $BOT_USER -

# Create backup script
log "Creating backup script..."
cat > $BOT_DIR/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/home/trading/victorychain_stack/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/config_backup_$DATE.tar.gz"

# Create backup of configuration and logs
tar -czf "$BACKUP_FILE" config.toml logs/

# Keep only last 7 backups
find "$BACKUP_DIR" -name "config_backup_*.tar.gz" -type f -mtime +7 -delete

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup created: $BACKUP_FILE" >> logs/backup.log
EOF

chmod +x $BOT_DIR/backup.sh
chown $BOT_USER:$BOT_USER $BOT_DIR/backup.sh

# Create daily backup cron job
crontab -u $BOT_USER -l 2>/dev/null | { cat; echo "0 2 * * * $BOT_DIR/backup.sh"; } | crontab -u $BOT_USER -

# Create environment file for API keys
log "Creating environment configuration..."
cat > $BOT_DIR/.env << EOF
# Binance US API Configuration
# IMPORTANT: Set these values before starting the bot
BINANCEUS_KEY=your_BINANCEUS_KEY_here
BINANCEUS_SECRET=your_BINANCEUS_SECRET_here

# Optional: Webhook for alerts
ALERT_WEBHOOK_URL=your_webhook_url_here
EOF

chown $BOT_USER:$BOT_USER $BOT_DIR/.env
chmod 600 $BOT_DIR/.env

# Create startup verification script
log "Creating startup verification script..."
cat > $BOT_DIR/verify_startup.sh << 'EOF'
#!/bin/bash

echo "VictoryChain Bot Startup Verification"
echo "====================================="

# Check if API keys are configured
if grep -q "your_BINANCEUS_KEY_here" .env || grep -q "your_BINANCEUS_SECRET_here" .env; then
    echo "❌ ERROR: Binance API keys not configured in .env file"
    echo "Please edit .env file and set your actual API keys"
    exit 1
fi

# Check if bot binary exists
if [ ! -f "target/release/backend" ]; then
    echo "❌ ERROR: Bot binary not found. Run: cargo build --release"
    exit 1
fi

# Check network connectivity to Binance US
if ! curl -s --max-time 10 https://api.binance.us/api/v3/ping > /dev/null; then
    echo "❌ ERROR: Cannot reach Binance US API"
    exit 1
fi

echo "✅ All checks passed! Bot is ready to start."
echo ""
echo "To start the bot:"
echo "  sudo systemctl start victorychain"
echo ""
echo "To check status:"
echo "  sudo systemctl status victorychain"
echo ""
echo "To view logs:"
echo "  journalctl -u victorychain -f"
EOF

chmod +x $BOT_DIR/verify_startup.sh
chown $BOT_USER:$BOT_USER $BOT_DIR/verify_startup.sh

# Create management scripts
log "Creating management scripts..."
cat > $BOT_DIR/manage.sh << 'EOF'
#!/bin/bash

SERVICE_NAME="victorychain"
LOG_DIR="logs"

case "$1" in
    start)
        echo "Starting VictoryChain Bot..."
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "Stopping VictoryChain Bot..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "Restarting VictoryChain Bot..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        echo "Recent logs (press Ctrl+C to exit):"
        journalctl -u $SERVICE_NAME -f
        ;;
    build)
        echo "Building bot..."
        cargo build --release
        ;;
    update)
        echo "Updating and rebuilding bot..."
        git pull
        cargo build --release
        sudo systemctl restart $SERVICE_NAME
        ;;
    check)
        ./verify_startup.sh
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|build|update|check}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the trading bot"
        echo "  stop    - Stop the trading bot"
        echo "  restart - Restart the trading bot"
        echo "  status  - Show bot status"
        echo "  logs    - Show live logs"
        echo "  build   - Build the bot"
        echo "  update  - Pull updates and restart"
        echo "  check   - Verify bot configuration"
        exit 1
        ;;
esac
EOF

chmod +x $BOT_DIR/manage.sh
chown $BOT_USER:$BOT_USER $BOT_DIR/manage.sh

log "Deployment complete!"
echo ""
echo -e "${GREEN}✅ VictoryChain Bot has been deployed successfully!${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT NEXT STEPS:${NC}"
echo "1. Configure your Binance US API keys:"
echo "   sudo -u $BOT_USER nano $BOT_DIR/.env"
echo ""
echo "2. Verify the configuration:"
echo "   sudo -u $BOT_USER $BOT_DIR/verify_startup.sh"
echo ""
echo "3. Start the bot:"
echo "   systemctl start $SERVICE_NAME"
echo ""
echo "4. Monitor the bot:"
echo "   journalctl -u $SERVICE_NAME -f"
echo ""
echo -e "${YELLOW}MANAGEMENT COMMANDS:${NC}"
echo "   sudo -u $BOT_USER $BOT_DIR/manage.sh {start|stop|restart|status|logs|build|update|check}"
echo ""
echo -e "${YELLOW}LOG LOCATIONS:${NC}"
echo "   System logs: journalctl -u $SERVICE_NAME"
echo "   Bot logs: $LOG_DIR/"
echo "   Monitor logs: $LOG_DIR/monitor.log"
echo ""
echo -e "${GREEN}The bot is configured to run 24/7 with automatic restart on failure.${NC}"
