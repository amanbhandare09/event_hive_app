#!/bin/bash

APP_DIR="/var/www/event_hive_app"

echo "Deleting old app"
sudo rm -rf $APP_DIR

echo "Creating app directory"
sudo mkdir -p $APP_DIR

echo "Copying new files"
sudo cp -r . $APP_DIR

cd $APP_DIR

# Rename env file to .env if exists
if [ -f env ]; then
    sudo mv env .env
fi

echo "Installing Python & pip"
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv

echo "Creating venv"
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing Nginx (if missing)"
sudo apt-get install -y nginx

# -------------------- NGINX CONFIG --------------------
NGINX_CONF="/etc/nginx/sites-available/event_hive_app"

sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/event_hive_app/app.sock;
    }
}
EOF

sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# -------------------- STOP PREVIOUS GUNICORN --------------------
echo "Stopping old Gunicorn"
sudo pkill -f gunicorn || true
sudo rm -f app.sock

# -------------------- START GUNICORN --------------------
echo "Starting Gunicorn"

sudo bash -c "cat > /etc/systemd/system/eventhive.service" <<EOF
[Unit]
Description=Event Hive Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:app.sock event_hive_app:app

Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable eventhive
sudo systemctl restart eventhive

echo "Deployment Completed Successfully 🚀"
