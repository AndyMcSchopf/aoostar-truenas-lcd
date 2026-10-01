#!/bin/bash
set -u
DIR=/app/cfg/sensors
while true; do
  tmp="$DIR/values.txt.tmp"
  cat "$DIR/hardware.txt" "$DIR/truenas.txt" 2>/dev/null | awk -F: '!seen[$1]++' > "$tmp"
  mv "$tmp" "$DIR/values.txt"
  sleep 1
done
