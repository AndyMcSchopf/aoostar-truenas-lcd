FROM debian:trixie-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential pkg-config libudev-dev git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH=/root/.cargo/bin:$PATH
RUN git clone --depth 1 https://github.com/zehnm/aoostar-rs.git /build/aoostar-rs && cd /build/aoostar-rs && cargo build --release

FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git python3 python3-pil python3-flask python3-flask-cors python3-websocket iproute2 procps && rm -rf /var/lib/apt/lists/*
COPY --from=builder /build/aoostar-rs/target/release/asterctl /usr/local/bin/asterctl
COPY --from=builder /build/aoostar-rs/target/release/aster-sysinfo /usr/local/bin/aster-sysinfo
RUN git clone --depth 1 https://github.com/xavtb78/aoostar-proxmox-lcd.git /tmp/upstream && \
    mkdir -p /defaults/cfg /app/cfg/sensors && \
    cp -a /tmp/upstream/cfg/. /defaults/cfg/ && cp /tmp/upstream/webui.py /app/webui.py && \
    sed -i 's/AOOSTAR Screen Editor v2/AOOSTAR TrueNAS Screen Editor/g; s/proxmox_panel.jpg/truenas_panel.jpg/g' /app/webui.py && \
    if [ -f /defaults/cfg/proxmox_panel.jpg ]; then cp /defaults/cfg/proxmox_panel.jpg /defaults/cfg/truenas_panel.jpg; fi && \
    sed -i 's/proxmox_/truenas_/g; s/Proxmox/TrueNAS/g; s/proxmox_panel.jpg/truenas_panel.jpg/g' /defaults/cfg/monitor.json /defaults/cfg/sensor-mapping.cfg 2>/dev/null || true && \
    rm -rf /tmp/upstream
COPY start.sh truenas-sensors.py merge-sensors.sh /app/
RUN chmod +x /app/start.sh /app/merge-sensors.sh
WORKDIR /app
EXPOSE 8765
CMD ["/app/start.sh"]
