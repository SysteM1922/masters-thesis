from multiprocessing import Process, Queue
import os
from dotenv import load_dotenv
from processing_unit import start_processing_unit

load_dotenv("../.env")

SIGNALING_IP = os.getenv("SIGNALING_SERVER_HOST")
SIGNALING_PORT = os.getenv("SIGNALING_SERVER_PORT")