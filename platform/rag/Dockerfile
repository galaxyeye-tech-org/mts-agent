FROM python:3.10.13-slim-bookworm
LABEL author="zhangyijun <zhangyijun@galaxyeye-tech.com>"

ENV APP_NAME="mts-agent-rag" \
    APP_VERSION="mts-agent-rag_version" \
    APP_DIR="/usr/local/mts-agent-rag" \
    HF_ENDPOINT=https://hf-mirror.com

COPY ./ ${APP_DIR}/
COPY docker-entrypoint.sh /usr/local/bin/

RUN apt-get update && \
    apt-get install gcc g++ make cmake -y && \
    pip3 install --upgrade pip && \
    pip3 install https://github.com/explosion/spacy-models/releases/download/zh_core_web_trf-3.7.2/zh_core_web_trf-3.7.2-py3-none-any.whl && \
    pip3 install https://github.com/explosion/spacy-models/releases/download/zh_core_web_lg-3.7.0/zh_core_web_lg-3.7.0-py3-none-any.whl && \
    pip3 install --no-cache-dir huggingface_hub && \
    mkdir /usr/local/models/bge-large-zh -p && \
    huggingface-cli download --resume-download BAAI/bge-large-zh --local-dir /usr/local/models/bge-large-zh && \
    pip3 install --no-cache-dir -r ${APP_DIR}/requirements.txt && \
    apt-get autoremove gcc g++ make cmake -y && \
    apt-get clean && \
    apt-get autoclean && \
    chmod 755 /usr/local/bin/docker-entrypoint.sh && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* ~/.cache/pip ${APP_DIR}/Dockerfile ${APP_DIR}/docker-entrypoint.sh

WORKDIR ${APP_DIR}

EXPOSE 9090

ENTRYPOINT ["docker-entrypoint.sh"]