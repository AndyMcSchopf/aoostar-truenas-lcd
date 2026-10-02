#!/bin/bash
set -u
VER=$(cat /app/VERSION 2>/dev/null || echo unknown)`necho "=== AOOSTAR TrueNAS LCD Manager v$VER ==="
RUNTIME=/run/aoostar; CFG=/app/cfg
mkdir -p "$RUNTIME" "$CFG/sensors" "$CFG/images" "$CFG/backups"
( while true; do aster-sysinfo --refresh 5 --out "$RUNTIME/hardware.txt"; sleep 5; done ) & SYS_PID=$!
export TRUENAS_SENSOR_OUT="$RUNTIME/truenas.txt"
( while true; do python3 /app/truenas-sensors.py; sleep 5; done ) & TN_PID=$!
( while true; do tmp="$CFG/sensors/.values.$$.tmp"; : > "$tmp"; [ -f "$RUNTIME/hardware.txt" ] && cat "$RUNTIME/hardware.txt" >> "$tmp"; [ -f "$RUNTIME/truenas.txt" ] && cat "$RUNTIME/truenas.txt" >> "$tmp"; mv -f "$tmp" "$CFG/sensors/values.txt"; sleep 2; done ) & MERGE_PID=$!
( while true; do python3 /app/history.py; sleep 5; done ) & HISTORY_PID=$!
( while true; do python3 /app/webui.py; sleep 3; done ) & WEB_PID=$!
sleep 3
( while true; do if [ -r "$CFG/monitor.json" ]; then asterctl --config "$CFG/monitor.json" --config-dir "$CFG" --font-dir /app/fonts --sensor-path "$CFG/sensors" --sensor-mapping "$CFG/sensor-mapping.cfg"; fi; sleep 5; done ) & LCD_PID=$!
cleanup(){ kill "$SYS_PID" "$TN_PID" "$MERGE_PID" "$HISTORY_PID" "$WEB_PID" "$LCD_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
wait
