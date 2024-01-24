FROM python:3.10.13-slim-bookworm
LABEL author="zhangyijun <zhangyijun@galaxyeye-tech.com>"

ENV APP_NAME="mts-agent" \
    APP_VERSION="mts-agent_version" \
    APP_DIR="/usr/local/mts-agent" \
    PYTHONPATH="/usr/local/mts-agent"

COPY ./ ${APP_DIR}/
COPY docker-entrypoint.sh /usr/local/bin/

RUN apt-get update && \
    apt-get install gcc g++ make cmake -y && \
    pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r ${APP_DIR}/requirements.txt && \
    apt-get autoremove gcc g++ make cmake -y && \
    apt-get clean && \
    apt-get autoclean && \
    chmod 755 /usr/local/bin/docker-entrypoint.sh && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache/pip ${APP_DIR}/Dockerfile ${APP_DIR}/docker-entrypoint.sh

WORKDIR ${APP_DIR}

EXPOSE 12400

ENTRYPOINT ["docker-entrypoint.sh"]