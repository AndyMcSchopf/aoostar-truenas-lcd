FROM rust:1-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends git pkg-config libudev-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /build
RUN git clone https://github.com/zehnm/aoostar-rs.git
WORKDIR /build/aoostar-rs
COPY patches/asterctl/main.rs /build/aoostar-rs/crates/asterctl/src/main.rs
COPY patches/asterctl/cfg.rs /build/aoostar-rs/crates/asterctl/src/cfg.rs
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
COPY app/roundtrip_selftest.py /app/roundtrip_selftest.py
COPY app/v0810_selftest.py /app/v0810_selftest.py
COPY app/v0811_selftest.py /app/v0811_selftest.py
COPY app/v0812_selftest.py /app/v0812_selftest.py
COPY app/v0813_selftest.py /app/v0813_selftest.py
COPY app/v089_selftest.py /app/v089_selftest.py
COPY app/v0891_selftest.py /app/v0891_selftest.py
COPY app/v0892_selftest.py /app/v0892_selftest.py
COPY app/data_binding_selftest.py /app/data_binding_selftest.py
COPY app/title_alignment_selftest.py /app/title_alignment_selftest.py
COPY app/factory_bootstrap.py /app/factory_bootstrap.py
COPY defaults/factory /defaults/factory
COPY app/templates /app/templates
COPY app/static /app/static

RUN chmod +x /app/start.sh
RUN python3 -m py_compile /app/webui.py /app/history.py /app/truenas-sensors.py /app/lcd_generator.py /app/render_shared.py /app/roundtrip_selftest.py
RUN python3 /app/roundtrip_selftest.py
RUN python3 /app/v0810_selftest.py
RUN python3 /app/v0811_selftest.py
RUN python3 /app/v0812_selftest.py
RUN python3 /app/v0813_selftest.py
RUN python3 /app/v089_selftest.py
RUN python3 /app/v0891_selftest.py
RUN python3 /app/v0892_selftest.py
RUN python3 /app/data_binding_selftest.py
RUN python3 /app/title_alignment_selftest.py
RUN bash -n /app/start.sh
RUN test -s /app/fonts/HarmonyOS_Sans_SC_Bold.ttf
RUN VERSION_VALUE="$(tr -d '\r\n' </app/VERSION)" && echo "Building AOOSTAR TrueNAS LCD v${VERSION_VALUE}" && printf '%s\n' "${VERSION_VALUE}" | grep -Eq '^[0-9]+(\.[0-9]+){2,}$'
RUN asterctl --help 2>&1 | grep -q -- '--config'
RUN asterctl --help 2>&1 | grep -q -- '--sensor-path'
RUN aster-sysinfo --help 2>&1 | grep -q -- '--out'

LABEL org.opencontainers.image.revision="${VCS_REF}"

WORKDIR /app
EXPOSE 8765
CMD ["/app/start.sh"]

COPY app/v090_selftest.py /app/v090_selftest.py
RUN python3 /app/v090_selftest.py
