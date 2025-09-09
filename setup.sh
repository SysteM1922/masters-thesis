#!/bin/bash

python3 -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \
deactivate

cd interface/gym
npm install
cd ../../signaling-server

python3 -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \
deactivate

cd ..

echo -e "\n\nPlease make sure to add the .env files in the root directory and in interface/gym"
