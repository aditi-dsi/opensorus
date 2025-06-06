echo "Deploying Webhook service..."

cp opensorus.service /etc/systemd/system/

systemctl daemon-reexec
systemctl daemon-reload

systemctl enable opensorus.service
systemctl restart opensorus.service

systemctl status opensorus.service