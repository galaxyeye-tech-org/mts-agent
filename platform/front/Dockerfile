FROM nginx:1.24.0-bullseye

ENV APP_DIR="/usr/local/mts_agent_web"

COPY ./dist/* ${APP_DIR}/
COPY default.conf /etc/nginx/conf.d/default.conf

WORKDIR ${APP_DIR}