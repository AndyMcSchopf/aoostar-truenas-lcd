FROM rust:1-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends git pkg-config libudev-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /build
RUN git clone https://github.com/zehnm/aoostar-rs.git
WORKDIR /build/aoostar-rs
RUN cargo build --release

FROM python:3.12-slim-bookworm
ARG VCS_REF=unknown
ENV AOOSTAR_BUILD=${VCS_REF}

RUN apt-get update && apt-get install -y --no-install-recommends libudev1 ca-certificates fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir flask pillow requests websocket-client

COPY --from=builder /build/aoostar-rs/target/release/asterctl /usr/local/bin/asterctl
COPY --from=builder /build/aoostar-rs/target/release/aster-sysinfo /usr/local/bin/aster-sysinfo
COPY --from=builder /build/aoostar-rs/fonts /app/fonts

COPY truenas-sensors.py lcd_generator.py start.sh /app/
COPY VERSION /app/VERSION
COPY app/webui.py app/history.py app/render_shared.py /app/
COPY app/templates /app/templates
COPY app/static /app/static

RUN chmod +x /app/start.sh
RUN python3 -m py_compile /app/webui.py /app/history.py /app/truenas-sensors.py /app/lcd_generator.py /app/render_shared.py
RUN bash -n /app/start.sh
RUN test -s /app/fonts/HarmonyOS_Sans_SC_Bold.ttf
RUN VERSION_VALUE="$(tr -d '\r\n' </app/VERSION)" && echo "Building AOOSTAR TrueNAS LCD v${VERSION_VALUE}" && printf '%s\n' "${VERSION_VALUE}" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?$'
RUN asterctl --help 2>&1 | grep -q -- '--config'
RUN asterctl --help 2>&1 | grep -q -- '--sensor-path'
RUN aster-sysinfo --help 2>&1 | grep -q -- '--out'

LABEL org.opencontainers.image.revision="${VCS_REF}"

WORKDIR /app
EXPOSE 8765
CMD ["/app/start.sh"]
