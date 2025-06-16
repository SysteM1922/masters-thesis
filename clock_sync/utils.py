import enum
import socket
import struct

MSG_SIZE = 9  # Size of the PTP message in bytes
SOCKET_TIMEOUT = 1  # seconds
MAX_CONNECTION_TRIES = 3 # Maximum number of tries to connect to the server
MAX_SYNC_TRIES = 10 # Maximum number of tries to synchronize with the server
MAX_WAIT_TRIES = 5 # Maximum number of tries to wait for a response from the client

# SO_TIMESTAMPING constants
SOF_TIMESTAMPING_TX_HARDWARE = 1
SOF_TIMESTAMPING_TX_SOFTWARE = 2
SOF_TIMESTAMPING_RX_HARDWARE = 4
SOF_TIMESTAMPING_RX_SOFTWARE = 8
SOF_TIMESTAMPING_SOFTWARE = 16
SOF_TIMESTAMPING_SYS_HARDWARE = 32
SOF_TIMESTAMPING_RAW_HARDWARE = 64

# Control message types
SCM_TIMESTAMPING = 37

class PTPMsgType(enum.Enum):
    """
    Enum for message types.
    """
    PTP_SYNC_REQUEST = 0x01
    PTP_SYNC_FOLLOW_UP = 0x02  # Same value as PTP_SYNC_REQUEST for compatibility
    PTP_SYNC_RESPONSE = 0x03
    PTP_DELAY_REQUEST = 0x04
    PTP_DELAY_RESPONSE = 0x05
    PTP_SYNC_COMPLETED = 0x06
    PTP_BUSY = 0x07

class PTPMessage:
    """
    Base class for PTP messages.
    """
    def __init__(self, msg_type: PTPMsgType, timestamp: int):
        self.msg_type = msg_type
        self.timestamp = timestamp

    def __repr__(self):
        return f"PTPMessage(msg_type={self.msg_type}, timestamp={self.timestamp})"

def setup_timestamping_socket(sock: socket.socket):
    """
    Configure socket for SO_TIMESTAMPING.
    """
    timestamping_flags = (SOF_TIMESTAMPING_RX_SOFTWARE | 
                         SOF_TIMESTAMPING_TX_SOFTWARE |
                         SOF_TIMESTAMPING_SOFTWARE)
    
    sock.setsockopt(socket.SOL_SOCKET, SCM_TIMESTAMPING, timestamping_flags)
    return sock

def extract_timestamp_from_cmsg(cmsg_list) -> float:
    """
    Extract timestamp from control message list.
    Returns timestamp in seconds as float.
    """
    for cmsg_level, cmsg_type, cmsg_data in cmsg_list:
        if cmsg_level == socket.SOL_SOCKET and cmsg_type == SCM_TIMESTAMPING:
            # Each timestamp is 16 bytes (8 bytes sec + 8 bytes nsec)
            # We want the software timestamp (index 0)
            if len(cmsg_data) >= 16:
                sec, nsec = struct.unpack('QQ', cmsg_data[:16])
                return sec + nsec / 1e9
    return None

def get_send_timestamp(sock: socket.socket) -> float:
    """
    Get send timestamp from socket error queue.
    Returns timestamp in seconds as float, or None if not available.
    """
    try:
        data, ancdata, msg_flags, addr = sock.recvmsg(1, 1024, socket.MSG_ERRQUEUE)
        timestamp = extract_timestamp_from_cmsg(ancdata)
        return timestamp
    except socket.error:
        return None

def receive_with_timestamp(sock: socket.socket, bufsize: int):
    """
    Receive data with kernel timestamp.
    Returns (data, addr, timestamp_ns) where timestamp_ns is in nanoseconds.
    """
    try:
        data, ancdata, msg_flags, addr = sock.recvmsg(bufsize, 1024)
        
        # Extract timestamp from control messages
        timestamp = extract_timestamp_from_cmsg(ancdata)
        if timestamp is not None:
            timestamp_ns = int(timestamp * 1e9)
        else:
            # Fallback to current time if no timestamp available
            timestamp_ns = get_current_time_ns()
            
        return data, addr, timestamp_ns
    except socket.error:
        raise

def get_current_time_ns() -> int:
    """
    Get current time in nanoseconds using kernel time.
    This is a fallback when timestamps are not available.
    """
    print("Using fallback for current time in nanoseconds.")
    import time
    return int(time.time() * 1e9)

def build_message(msg_type: PTPMsgType, timestamp: int) -> bytearray:
    """
    Send a PTP message to the specified address.
    """
    message = bytearray(MSG_SIZE)
    message[0] = msg_type.value
    message[1:9] = timestamp.to_bytes(8, 'big')
    
    return message

def send_message(sock: socket.socket, message: bytes, addr: tuple):
    """
    Send a PTP message to the specified address.
    """

    sock.sendto(message, addr)

def clear_error_queue(sock: socket.socket):
    """
    Clear the error queue of the socket.
    This is useful to avoid stale timestamps.
    """
    try:
        while True:
            sock.recvmsg(1, 1024, socket.MSG_ERRQUEUE)
    except socket.error:
        pass  # Ignore errors when clearing the queue

    return

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