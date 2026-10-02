FROM debian:trixie-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential pkg-config libudev-dev git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH=/root/.cargo/bin:$PATH
RUN git clone --depth 1 https://github.com/zehnm/aoostar-rs.git /build/aoostar-rs && cd /build/aoostar-rs && cargo build --release

FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git python3 python3-pil python3-flask python3-flask-cors python3-websocket iproute2 procps fonts-noto-core && rm -rf /var/lib/apt/lists/*
COPY --from=builder /build/aoostar-rs/target/release/asterctl /usr/local/bin/asterctl
COPY --from=builder /build/aoostar-rs/target/release/aster-sysinfo /usr/local/bin/aster-sysinfo
RUN git clone --depth 1 https://github.com/xavtb78/aoostar-proxmox-lcd.git /tmp/upstream && \
    mkdir -p /defaults/cfg /app/cfg/sensors && \
    cp -a /tmp/upstream/cfg/. /defaults/cfg/ && cp /tmp/upstream/webui.py /app/webui.py && \
    if [ -f /defaults/cfg/proxmox_panel.jpg ]; then cp /defaults/cfg/proxmox_panel.jpg /defaults/cfg/truenas_panel.jpg; fi && \
    sed -i 's/proxmox_/truenas_/g; s/Proxmox/TrueNAS/g; s/proxmox_panel.jpg/truenas_panel.jpg/g' /defaults/cfg/monitor.json /defaults/cfg/sensor-mapping.cfg 2>/dev/null || true && \
    rm -rf /tmp/upstream
COPY localize-webui.py /tmp/localize-webui.py
RUN python3 /tmp/localize-webui.py && rm /tmp/localize-webui.py
COPY start.sh truenas-sensors.py merge-sensors.sh /app/
RUN mkdir -p /app/fonts && ln -sf /usr/share/fonts/truetype/noto/NotoSans-Bold.ttf /app/fonts/HarmonyOS_Sans_SC_Bold.ttf
RUN chmod +x /app/start.sh /app/merge-sensors.sh
WORKDIR /app
EXPOSE 8765
CMD ["/app/start.sh"]

# v0.4 additions
COPY webui_de.py /app/webui_de.py
COPY defaults-v0.4.json /app/defaults-v0.4.json


# v0.4.1 build gate: reject syntactically broken Python images
RUN python3 -m py_compile /app/truenas-sensors.py /app/webui.py


# v0.5 standalone German WebUI
COPY webui_v05.py /app/webui_v05.py
RUN mkdir -p /app/presets
COPY truenas-de-v0.5.json /app/presets/truenas-de-v0.5.json
RUN python3 -m py_compile /app/webui_v05.py /app/truenas-sensors.py

# v0.5.1 start.sh portability gate
RUN sed -i '1s/^\xEF\xBB\xBF//' /app/start.sh \
    && sed -i 's/\r$//' /app/start.sh \
    && chmod +x /app/start.sh \
    && head -n 1 /app/start.sh | grep -Eq '^#!(/bin/bash|/usr/bin/env bash)$' \
    && bash -n /app/start.sh

# v0.6 visual editor
COPY webui_v06.py /app/webui_v06.py
RUN python3 -m py_compile /app/webui_v06.py /app/truenas-sensors.py

# v0.6.1 native LCD editor
COPY webui_v061.py /app/webui_v061.py
RUN python3 -m py_compile /app/webui_v061.py /app/truenas-sensors.py

# v0.6.2 enterprise dark
COPY webui_v062.py /app/webui_v062.py
RUN python3 -m py_compile /app/webui_v062.py /app/truenas-sensors.py

# v0.6.3 enterprise design system
COPY webui_v063.py /app/webui_v063.py
RUN python3 -m py_compile /app/webui_v063.py /app/truenas-sensors.py

# v0.7 consolidation
COPY webui_v07.py /app/webui_v07.py
RUN python3 -m py_compile /app/webui_v07.py /app/truenas-sensors.py
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh && bash -n /app/start.sh

# v0.7.1 aster-sysinfo CLI gate
RUN bash -n /app/start.sh && aster-sysinfo --help 2>&1 | grep -q -- '--out'

# v0.7.2 runtime storage gate
RUN bash -n /app/start.sh && python3 -m py_compile /app/truenas-sensors.py /app/webui_v07.py
RUN aster-sysinfo --help 2>&1 | grep -q -- '--out'

# v0.7.3 asterctl 0.2.x CLI compatibility gate
RUN bash -n /app/start.sh \
    && asterctl --help 2>&1 | grep -q -- '--config' \
    && asterctl --help 2>&1 | grep -q -- '--config-dir' \
    && asterctl --help 2>&1 | grep -q -- '--font-dir' \
    && asterctl --help 2>&1 | grep -q -- '--sensor-path' \
    && asterctl --help 2>&1 | grep -q -- '--sensor-mapping' \
    && ! grep -Eq 'asterctl[[:space:]]+lcd' /app/start.sh

# v0.7.4 webui gate
RUN python3 -m py_compile /app/webui_v07.py
RUN grep -q 'async function init' /app/webui_v07.py && grep -q 'uploadImage' /app/webui_v07.py

# v0.7.5 editor gate
RUN python3 -m py_compile /app/webui_v07.py
RUN grep -q 'function renderInspector' /app/webui_v07.py && grep -q 'function sparkHTML' /app/webui_v07.py && grep -q 'function imageProp' /app/webui_v07.py && grep -q 'function dragElement' /app/webui_v07.py

# v0.7.6 LCD generator
COPY lcd_generator.py /app/lcd_generator.py
RUN python3 -m py_compile /app/lcd_generator.py /app/webui_v07.py
RUN grep -q '/api/lcd/generate' /app/webui_v07.py && grep -q 'mode.*3' /app/lcd_generator.py

# v0.7.7 UI cleanup gate
RUN python3 -m py_compile /app/webui_v07.py
RUN grep -q 'v0.7.7 UI cleanup' /app/webui_v07.py && grep -q 'LCD-VORSCHAU ERZEUGEN' /app/webui_v07.py
