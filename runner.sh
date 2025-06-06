echo "Deploying Webhook service..."

cp opensorus.service /etc/systemd/system/

systemctl daemon-reexec
systemctl daemon-reload

systemctl enable opensorus.service
systemctl start opensorus.service

systemctl status opensorus.service