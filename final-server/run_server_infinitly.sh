#!/bin/bash
while true; do
    python3 server.py
    echo "Server crashed with exit code $?.  Respawning.." >&2
    sleep 1
done