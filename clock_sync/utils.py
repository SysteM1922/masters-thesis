import enum
import time

MSG_SIZE = 9  # Size of the PTP message in bytes
SOCKET_TIMEOUT = 1  # seconds
MAX_CONNECTION_TRIES = 3 # Maximum number of tries to connect to the server
MAX_SYNC_TRIES = 10 # Maximum number of tries to synchronize with the server
MAX_WAIT_TRIES = 5 # Maximum number of tries to wait for a response from the client

class PTPMsgType(enum.Enum):
    """
    Enum for message types.
    """
    PTP_SYNC_REQUEST = 0x00
    PTP_SYNC_RESPONSE = 0x01
    PTP_DELAY_REQUEST = 0x02
    PTP_DELAY_RESPONSE = 0x03
    PTP_SYNC_COMPLETED = 0x04
    PTP_BUSY = 0x05

class PTPMessage:
    """
    Base class for PTP messages.
    """
    def __init__(self, msg_type: PTPMsgType, timestamp: int):
        self.msg_type = msg_type
        self.timestamp = timestamp

    def __repr__(self):
        return f"PTPMessage(msg_type={self.msg_type}, timestamp={self.timestamp})"

def get_current_time() -> float:
    return time.time()

def build_message(msg_type: PTPMsgType, timestamp: int) -> bytearray:
    """
    Send a PTP message to the specified address.
    """
    message = bytearray(MSG_SIZE)
    message[0] = msg_type.value
    message[1:9] = timestamp.to_bytes(8, 'big')
    
    return message

def parse_message(data: bytes) -> PTPMessage:
    """
    Parse a PTP message from bytes.
    """
    if len(data) < MSG_SIZE:
        raise ValueError("Data is too short to be a valid PTP message.")
    
    msg_type = PTPMsgType(data[0])
    timestamp = int.from_bytes(data[1:9], 'big')
    
    return PTPMessage(msg_type, timestamp)

def parse_message_raw(data: bytes) -> tuple:
    """
    Parse a PTP message from bytes without creating a PTPMessage object.
    """
    if len(data) < MSG_SIZE:
        raise ValueError("Data is too short to be a valid PTP message.")
    
    msg_type = data[0]
    timestamp = int.from_bytes(data[1:9], 'big')
    
    return msg_type, timestamp