#!/bin/bash
# InvestRight Trading API — EC2 Setup & Startup Script
# Usage: chmod +x ec2-startup.sh && sudo ./ec2-startup.sh
# Tested on: Amazon Linux 2023, Ubuntu 22.04

set -euo pipefail

APP_NAME="investright-trading-api"
APP_DIR="/opt/${APP_NAME}"
APP_USER="investright"
JAR_FILE="${APP_DIR}/app.jar"
ENV_FILE="${APP_DIR}/.env"
TRADES_DIR="${APP_DIR}/trades"
LOG_DIR="/var/log/${APP_NAME}"

echo "=========================================="
echo " InvestRight Trading API — EC2 Setup"
echo "=========================================="

# ---- Detect OS ----
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="${ID}"
else
    OS_ID="unknown"
fi
echo "Detected OS: ${OS_ID}"

# ---- Install Java 17 ----
echo "[1/6] Installing Java 17..."
if command -v java &>/dev/null && java -version 2>&1 | grep -q "17"; then
    echo "  Java 17 already installed."
else
    case "${OS_ID}" in
        amzn)
            yum install -y java-17-amazon-corretto-headless
            ;;
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y openjdk-17-jre-headless
            ;;
        *)
            echo "  Unsupported OS. Install Java 17 manually."
            exit 1
            ;;
    esac
fi
java -version

# ---- Install Tesseract OCR ----
echo "[2/6] Installing Tesseract OCR..."
if command -v tesseract &>/dev/null; then
    echo "  Tesseract already installed."
else
    case "${OS_ID}" in
        amzn)
            yum install -y tesseract
            ;;
        ubuntu|debian)
            apt-get install -y tesseract-ocr tesseract-ocr-eng
            ;;
    esac
fi
tesseract --version

# ---- Create app user & directories ----
echo "[3/6] Setting up application directories..."
id "${APP_USER}" &>/dev/null || useradd -r -s /sbin/nologin "${APP_USER}"
mkdir -p "${APP_DIR}" "${TRADES_DIR}" "${LOG_DIR}"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}" "${LOG_DIR}"

# ---- Create environment file template ----
echo "[4/6] Creating environment configuration..."
if [ ! -f "${ENV_FILE}" ]; then
    cat > "${ENV_FILE}" << 'ENVEOF'
# InvestRight Trading API — Environment Variables
# Fill in your credentials below and restart the service.

# InvestRight API credentials
# Option A: Use AWS Secrets Manager (recommended — uncomment below)
AWS_SECRETS_MANAGER_ENABLED=true
AWS_SECRET_NAME=investright/trading-api/credentials
AWS_REGION=ap-south-1
# Option B: Set credentials directly (less secure)
# IR_API_KEY=your_api_key_here
# IR_API_SECRET=your_api_secret_here
# IR_USERNAME=your_username_here
# IR_PASSWORD=your_password_here
# IR_2FA_ANSWER=your_mpin_here

# Scheduler (set to true to enable automated trading)
SCHEDULER_ENABLED=true

# Trade signals folder
TRADE_FOLDER_PATH=/opt/investright-trading-api/trades

# Trade signal source: local, s3, or cloud
TRADE_IMAGE_SOURCE=local

# S3 configuration (only if TRADE_IMAGE_SOURCE=s3)
# AWS_REGION=ap-south-1
# S3_BUCKET_NAME=your-bucket-name
# S3_PREFIX=trade-signals/
# AWS credentials — use IAM role (recommended) or set these:
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key

# JVM memory settings
JAVA_OPTS=-Xms256m -Xmx512m

# Price check interval (ms)
PRICE_CHECK_INTERVAL_MS=5000

# Capital per trade (INR)
CAPITAL_PER_TRADE=100000
ENVEOF
    chmod 600 "${ENV_FILE}"
    chown "${APP_USER}:${APP_USER}" "${ENV_FILE}"
    echo "  Created ${ENV_FILE} — EDIT THIS FILE with your credentials!"
else
    echo "  ${ENV_FILE} already exists. Skipping."
fi

# ---- Create systemd service ----
echo "[5/6] Creating systemd service..."
cat > /etc/systemd/system/${APP_NAME}.service << SVCEOF
[Unit]
Description=InvestRight Trading API
After=network.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=/usr/bin/java \$JAVA_OPTS -jar ${JAR_FILE}
SuccessExitStatus=143
Restart=on-failure
RestartSec=10
StandardOutput=append:${LOG_DIR}/stdout.log
StandardError=append:${LOG_DIR}/stderr.log

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=${APP_DIR} ${LOG_DIR}

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable "${APP_NAME}"

# ---- Create cost-saving cron (start at 8:50 AM, stop at 3:35 PM IST) ----
echo "[6/6] Setting up log rotation..."
cat > /etc/logrotate.d/${APP_NAME} << LOGEOF
${LOG_DIR}/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    copytruncate
}
LOGEOF

echo ""
echo "=========================================="
echo " Setup Complete!"
echo "=========================================="
echo ""
echo " Next steps:"
echo "  1. Copy your JAR file to: ${JAR_FILE}"
echo "     scp target/${APP_NAME}-0.0.1-SNAPSHOT.jar ec2-user@<ip>:${JAR_FILE}"
echo ""
echo "  2. Edit your credentials:"
echo "     sudo nano ${ENV_FILE}"
echo ""
echo "  3. Start the service:"
echo "     sudo systemctl start ${APP_NAME}"
echo ""
echo "  4. Check logs:"
echo "     tail -f ${LOG_DIR}/stdout.log"
echo ""
echo "  5. Upload trade signal files to: ${TRADES_DIR}/"
echo "     scp signals.csv ec2-user@<ip>:${TRADES_DIR}/"
echo ""
echo "  6. (Optional) To save costs, stop EC2 after market hours:"
echo "     Create an EventBridge rule to start at 8:45 AM IST and stop at 3:40 PM IST"
echo ""
