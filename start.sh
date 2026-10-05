#!/bin/bash
set -u
VER="$(tr -d '\r\n' < /app/VERSION 2>/dev/null || printf unknown)"
BUILD="${AOOSTAR_BUILD:-unknown}"
ASTER_VER="$(asterctl --version 2>/dev/null || printf unknown)"
echo "===================================================="
echo " AOOSTAR TrueNAS LCD Manager"
echo " Version:    ${VER}"
echo " Build:      ${BUILD}"
echo " asterctl:   ${ASTER_VER}"
echo " Display:    960x376"
echo " Config:     /app/cfg/monitor.json"
echo " Web Editor: http://<TRUENAS-IP>:8765"
echo " History:    enabled / 120 samples"
echo "===================================================="

RUNTIME=/run/aoostar
CFG=/app/cfg
mkdir -p "$RUNTIME" "$CFG/sensors" "$CFG/images" "$CFG/backups"

( while true; do aster-sysinfo --refresh 5 --out "$RUNTIME/hardware.txt"; echo "[manager] aster-sysinfo restart" >&2; sleep 5; done ) & SYS_PID=$!
export TRUENAS_SENSOR_OUT="$RUNTIME/truenas.txt"
( while true; do python3 /app/truenas-sensors.py; echo "[manager] truenas-sensors restart" >&2; sleep 5; done ) & TN_PID=$!
( while true; do
    tmp="$CFG/sensors/.values.$$.tmp"; : > "$tmp"
    [ -f "$RUNTIME/hardware.txt" ] && cat "$RUNTIME/hardware.txt" >> "$tmp"
    [ -f "$RUNTIME/truenas.txt" ] && cat "$RUNTIME/truenas.txt" >> "$tmp"
    raw_uptime="$(awk -F': ' '$1=="truenas_uptime"{sub(/^[^:]*: /,"");print;exit}' "$tmp" 2>/dev/null || true)"
    if [ -n "$raw_uptime" ]; then
        short_uptime="$(printf '%s' "$raw_uptime" | awk -F'[:, ]+' '{ if ($2=="days" || $2=="day") printf "%sd %sh",$1,$3; else printf "%sh %02dm",$1,$2 }')"
        printf 'truenas_uptime_short: %s\n' "$short_uptime" >> "$tmp"
    fi
    mv -f "$tmp" "$CFG/sensors/values.txt"
    sleep 2
done ) & MERGE_PID=$!
( while true; do python3 /app/history.py; echo "[manager] history restart" >&2; sleep 5; done ) & HISTORY_PID=$!
( while true; do python3 /app/webui.py; echo "[manager] webui restart" >&2; sleep 3; done ) & WEB_PID=$!

sleep 3
( while true; do
    if [ ! -r "$CFG/monitor.json" ]; then echo "[manager] monitor.json missing" >&2; sleep 5; continue; fi
    rm -f "$RUNTIME/reload-lcd"
    asterctl --config "$CFG/monitor.json" --config-dir "$CFG" --font-dir /app/fonts --sensor-path "$CFG/sensors" --sensor-mapping "$CFG/sensor-mapping.cfg" &
    ASTER_PID=$!
    while kill -0 "$ASTER_PID" 2>/dev/null; do
        if [ -f "$RUNTIME/reload-lcd" ]; then
            rm -f "$RUNTIME/reload-lcd"
            echo "[manager] LCD reload requested" >&2
            kill "$ASTER_PID" 2>/dev/null || true
            wait "$ASTER_PID" 2>/dev/null || true
            break
        fi
        sleep 1
    done
    wait "$ASTER_PID" 2>/dev/null || true
    echo "[manager] asterctl restart" >&2
    sleep 1
done ) & LCD_PID=$!

cleanup(){ kill "$SYS_PID" "$TN_PID" "$MERGE_PID" "$HISTORY_PID" "$WEB_PID" "$LCD_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
wait
