#!/bin/bash
# 

set -e

python ${APP_DIR}/services_main.py

exec "$@"
