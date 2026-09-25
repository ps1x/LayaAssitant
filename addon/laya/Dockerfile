FROM python:3.12-slim-bookworm

ARG BUILD_VERSION=0.1.0

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="app" \
      io.hass.name="Laya Server" \
      io.hass.description="Local Laya decision API" \
      io.hass.url="https://github.com/ps1x/LayaAssitant" \
      io.hass.arch="amd64|aarch64"

RUN python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch==2.14.0+cpu" \
    && python -m pip install --no-cache-dir "laya[serve]==0.3.20" "transformers==5.17.0"

COPY run.sh /run.sh
RUN chmod 755 /run.sh && mkdir -p /data

EXPOSE 8000
CMD ["/run.sh"]
