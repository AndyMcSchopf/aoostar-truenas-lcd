#!/bin/bash
set -u
echo "=== AOOSTAR TrueNAS LCD Manager v0.7.2 ==="
RUNTIME=/run/aoostar
CFG=/app/cfg
mkdir -p "$RUNTIME" "$CFG/sensors" "$CFG/images" "$CFG/backups"
( while true; do aster-sysinfo --refresh 5 --out "$RUNTIME/hardware.txt"; echo "[manager] aster-sysinfo restart" >&2; sleep 5; done ) & SYS_PID=$!
export TRUENAS_SENSOR_OUT="$RUNTIME/truenas.txt"
( while true; do python3 /app/truenas-sensors.py; echo "[manager] truenas-sensors restart" >&2; sleep 5; done ) & TN_PID=$!
( while true; do tmp="$CFG/sensors/.values.$$.tmp"; : > "$tmp"; [ -f "$RUNTIME/hardware.txt" ] && cat "$RUNTIME/hardware.txt" >> "$tmp"; [ -f "$RUNTIME/truenas.txt" ] && cat "$RUNTIME/truenas.txt" >> "$tmp"; mv -f "$tmp" "$CFG/sensors/values.txt"; sleep 2; done ) & MERGE_PID=$!
( while true; do python3 /app/webui_v07.py; echo "[manager] webui restart" >&2; sleep 3; done ) & WEB_PID=$!
echo "Web Editor: http://<TRUENAS-IP>:8765"
sleep 3
( while true; do if [ ! -r "$CFG/monitor.json" ]; then echo "[manager] monitor.json missing" >&2; sleep 5; continue; fi; asterctl lcd --config "$CFG/monitor.json" --font-dir /app/fonts; echo "[manager] asterctl restart" >&2; sleep 5; done ) & LCD_PID=$!
cleanup(){ kill "$SYS_PID" "$TN_PID" "$MERGE_PID" "$WEB_PID" "$LCD_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
wait
