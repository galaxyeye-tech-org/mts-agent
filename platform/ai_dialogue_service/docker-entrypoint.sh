#!/bin/bash
# 

set -e

python ${APP_DIR}/app.py

exec "$@"
