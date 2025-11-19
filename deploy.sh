#!/bin/bash
set -e  # Exit on any error

# Configuration
APP_DIR="/var/www/event_hive_app"
SOCK_FILE="app.sock"
SERVICE_NAME="eventhive"
BACKUP_DIR="/var/backups/event_hive_app"

echo "🚀 Starting deployment..."

# Create backup of existing app (if exists)
if [ -d "$APP_DIR" ]; then
    echo "📦 Creating backup of existing app..."
    sudo mkdir -p $BACKUP_DIR
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    sudo tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$APP_DIR" . 2>/dev/null || true
    # Keep only last 5 backups
    sudo ls -t $BACKUP_DIR/backup_*.tar.gz | tail -n +6 | xargs -r sudo rm
fi

echo "🗑️  Deleting old app directory..."
sudo rm -rf $APP_DIR

echo "📁 Creating app directory..."
sudo mkdir -p $APP_DIR

echo "📋 Copying new files..."
sudo cp -r ./* $APP_DIR/
cd $APP_DIR

# Rename env file if exists
if [ -f env ]; then
    echo "🔧 Renaming env to .env..."
    sudo mv env .env
fi

# Set proper permissions
echo "🔒 Setting permissions..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR

echo "🐍 Installing Python & pip..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv

echo "🌐 Creating virtual environment..."
sudo -u www-data python3 -m venv venv

echo "📦 Installing dependencies..."
sudo -u www-data bash << 'EOF'
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Ensure gunicorn is installed
EOF

echo "🌍 Installing Nginx..."
sudo apt-get install -y nginx

# Nginx configuration
echo "⚙️  Configuring Nginx..."
NGINX_CONF="/etc/nginx/sites-available/$SERVICE_NAME"
sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/event_hive_access.log;
    error_log /var/log/nginx/event_hive_error.log;

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/$SOCK_FILE;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # Static files (if you have any)
    location /static {
        alias $APP_DIR/static;
        expires 30d;
    }

    # Health check endpoint
    location /health {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/$SOCK_FILE;
        access_log off;
    }

    # Increase max upload size if needed
    client_max_body_size 10M;
}
EOF

# Enable site
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/

# Remove default nginx site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx

# Stop old Gunicorn processes
echo "🛑 Stopping old Gunicorn processes..."
sudo pkill -f gunicorn || true
sudo rm -f $APP_DIR/$SOCK_FILE

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo bash -c "cat > /etc/systemd/system/$SERVICE_NAME.service" <<EOF
[Unit]
Description=Event Hive Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:$APP_DIR/$SOCK_FILE --timeout 120 --access-logfile /var/log/event_hive_access.log --error-logfile /var/log/event_hive_error.log app_run:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "✅ Enabling service..."
sudo systemctl enable $SERVICE_NAME

echo "🚀 Starting service..."
sudo systemctl restart $SERVICE_NAME

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check service status
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service is running!"
    sudo systemctl status $SERVICE_NAME --no-pager -l
else
    echo "❌ Service failed to start!"
    sudo journalctl -u $SERVICE_NAME -n 50 --no-pager
    exit 1
fi

# Check if socket file exists
if [ -S "$APP_DIR/$SOCK_FILE" ]; then
    echo "✅ Socket file created successfully"
else
    echo "⚠️  Warning: Socket file not found"
fi

# Test application
echo "🧪 Testing application..."
sleep 2
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Application health check passed!"
else
    echo "⚠️  Warning: Health check failed (make sure /health endpoint exists)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 App directory: $APP_DIR"
echo "🔌 Socket file: $APP_DIR/$SOCK_FILE"
echo "📊 Service status: sudo systemctl status $SERVICE_NAME"
echo "📋 View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "🌐 Nginx logs: /var/log/nginx/event_hive_*.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
