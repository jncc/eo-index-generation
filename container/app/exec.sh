#!/bin/bash

RENV_PATHS_ROOT=app/r-functions/renv
umask 002
cd /app
PYTHONPATH='.' luigi "$@"