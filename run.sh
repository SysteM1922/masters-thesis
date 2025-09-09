cd signaling-server
source venv/bin/activate && \
python3 signaling_server.py &

cd ..
deactivate
source venv/bin/activate && \
cd final-server
python3 multi_server.py &
deactivate

cd ../interface/gym
npm run dev && \

cd ../../