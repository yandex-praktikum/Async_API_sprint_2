#!/bin/bash

LOG_LEVEL=${PROJECT_LOG_LEVEL:-warning}
PORT=${PROJECT_PORT:-8000}

uvicorn --log-level=$LOG_LEVEL --port=$PORT --host='0.0.0.0' --log-config=core/log_config.json main:app