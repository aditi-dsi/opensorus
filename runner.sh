echo "Deploying Proxy WebSocket service..."

sudo cp opensorus.service /etc/systemd/system/

sudo systemctl daemon-reexec
sudo systemctl daemon-reload

sudo systemctl enable opensorus.service
sudo systemctl start opensorus.service

sudo systemctl status opensorus.service