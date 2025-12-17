#!/usr/bin/env bash
# start two clients in background: pong and ping
echo "[INFO] Lancement du client PONG..."
python client.py --role pong --topic lab/first_contact/hello &
sleep 1
echo "[INFO] Lancement du client PING..."
python client.py --role ping --topic lab/first_contact/hello





