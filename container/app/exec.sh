#!/bin/bash

RENV_PATHS_ROOT=/app/renv
umask 002
cd /app
PYTHONPATH='.' luigi --module workflow "$@"