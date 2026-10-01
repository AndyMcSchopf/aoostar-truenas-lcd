#!/bin/bash
set -u
CFG=/app/cfg
SENS=$CFG/sensors
mkdir -p "$SENS"
# Seed persistent config only on first start.
for f in /defaults/cfg/*; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  [ -e "$CFG/$base" ] || cp -a "$f" "$CFG/$base"
done
mkdir -p "$SENS"
touch "$SENS/hardware.txt" "$SENS/truenas.txt" "$SENS/values.txt"

echo "=== AOOSTAR TrueNAS LCD Manager ==="
if [ ! -e "${LCD_DEVICE:-/dev/ttyACM0}" ]; then
  echo "WARNING: LCD device ${LCD_DEVICE:-/dev/ttyACM0} not found; Web Editor will still start."
fi

aster-sysinfo --refresh "${REFRESH_SECONDS:-5}" -o "$SENS/hardware.txt" --temp-dir "$SENS/" &
python3 /app/truenas-sensors.py &
/app/merge-sensors.sh &
sleep 3

if [ -e "${LCD_DEVICE:-/dev/ttyACM0}" ]; then
  asterctl --config-dir "$CFG" --font-dir /app/fonts --config monitor.json --sensor-path "$SENS/values.txt" --sensor-mapping "$CFG/sensor-mapping.cfg" &
fi

echo "Web Editor: http://<TRUENAS-IP>:8765"
exec python3 /app/webui_v05.py

