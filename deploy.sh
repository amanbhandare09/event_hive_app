#!/bin/bash

APP_DIR="/var/www/event_hive_app"
SOCK_FILE="app.sock"

echo "Deleting old app"
sudo rm -rf $APP_DIR

echo "Creating app directory"
sudo mkdir -p $APP_DIR

echo "Copying new files"
sudo cp -r ./* $APP_DIR

cd $APP_DIR

# Rename env file if exists
if [ -f env ]; then
    sudo mv env .env
fi

echo "Installing Python & pip"
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv

echo "Creating virtual environment"
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing Nginx"
sudo apt-get install -y nginx

# Nginx configuration
NGINX_CONF="/etc/nginx/sites-available/event_hive_app"

sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/$SOCK_FILE;
    }
}
EOF

sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Stop old Gunicorn
sudo pkill -f gunicorn || true
sudo rm -f $SOCK_FILE

# Create systemd service
sudo bash -c "cat > /etc/systemd/system/eventhive.service" <<EOF
[Unit]
Description=Event Hive Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=$APP_DIR
Environment=\"PATH=$APP_DIR/venv/bin\"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:$SOCK_FILE app:app

Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable eventhive
sudo systemctl restart eventhive

echo "Deployment completed ✅"
