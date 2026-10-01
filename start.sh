#!/bin/bash
set -e
echo "=== AOOSTAR TrueNAS LCD Manager v0.7 ==="
mkdir -p /app/cfg/sensors /app/cfg/images /app/cfg/backups

aster-sysinfo --refresh 5000 --out /app/cfg/sensors/hardware.txt &
ASTER_SYSINFO_PID=$!

python3 /app/truenas-sensors.py &
TRUENAS_PID=$!

python3 /app/webui_v07.py &
WEB_PID=$!

echo "Web Editor: http://<TRUENAS-IP>:8765"

sleep 3
asterctl lcd --config /app/cfg/monitor.json --font-dir /app/fonts &
LCD_PID=$!

trap 'kill $ASTER_SYSINFO_PID $TRUENAS_PID $WEB_PID $LCD_PID 2>/dev/null || true' EXIT INT TERM
wait -n $ASTER_SYSINFO_PID $TRUENAS_PID $WEB_PID $LCD_PID
exit $?
