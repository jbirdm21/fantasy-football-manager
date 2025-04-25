#!/bin/bash
# Install the Fantasy Football Manager service for continuous running

# Exit on error
set -e

# Define paths
SERVICE_NAME="fantasy-football-manager"
SERVICE_FILE="scripts/systemd/$SERVICE_NAME.service"
SYSTEM_SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Get the current directory
CURRENT_DIR=$(pwd)

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
  echo "Service file not found: $SERVICE_FILE"
  exit 1
fi

# Create user and group if they don't exist
if ! id "ffm" &>/dev/null; then
  echo "Creating ffm user..."
  useradd -r -s /bin/false ffm
fi

# Install service file
echo "Installing service file to $SYSTEM_SERVICE_PATH..."
# Replace placeholders in the service file
sed "s|/opt/fantasy-football-manager|$CURRENT_DIR|g" "$SERVICE_FILE" > "$SYSTEM_SERVICE_PATH"

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable and start the service
echo "Enabling and starting service..."
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

echo "Service installed and started successfully!"
echo "Check status with: systemctl status $SERVICE_NAME"
echo "View logs with: journalctl -u $SERVICE_NAME" 