#!/bin/bash
# 

set -e

gunicorn main:app -c ${APP_DIR}/gunicorn.config.py --timeout 600
exec "$@"
