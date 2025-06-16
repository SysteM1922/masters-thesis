import time
import utils
import socket

IP = '0.0.0.0'
PORT = 8888

busy = False
actual_client = None

def create_server_socket():
    """
    Create a UDP server socket with timestamping enabled.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(utils.SOCKET_TIMEOUT)
    
    # Enable SO_TIMESTAMPING
    utils.setup_timestamping_socket(sock)
    
    sock.bind((IP, PORT))
    return sock

def receive_with_timestamp(sock: socket.socket):
    """
    Receive data with kernel timestamp.
    Returns (data, addr, timestamp_ns) where timestamp_ns is in nanoseconds.
    """
    return utils.receive_with_timestamp(sock, utils.MSG_SIZE)

def handle_message(data: bytes, addr: tuple, sock: socket.socket, arrival_time_ns: int):
    """
    Handle incoming messages and send appropriate responses.
    """
    global busy, actual_client
    msg_type = data[0]

    print(f"Received message from {addr}: type={msg_type}, client={addr}")
    
    if addr != actual_client:
        if busy:
            print(f"Server is busy, sending busy response to {addr}.")
            response = utils.build_message(utils.PTPMsgType.PTP_BUSY, 0)
            utils.send_message(sock, response, addr)
            return
        else:
            print(f"New client {addr} connected.")
            actual_client = addr
            busy = True

    if msg_type == utils.PTPMsgType.PTP_SYNC_REQUEST.value:
        response = utils.build_message(utils.PTPMsgType.PTP_SYNC_RESPONSE, 0)
        utils.send_message(sock, response, addr)
        print(f"Sent sync response to {addr}.")
        
        timestamp = int(utils.get_send_timestamp(sock) * 1e9)  # Convert to nanoseconds

        response = utils.build_message(utils.PTPMsgType.PTP_SYNC_FOLLOW_UP, timestamp)
        utils.send_message(sock, response, addr)
        print(f"Sent sync follow-up to {addr}.")
    elif msg_type == utils.PTPMsgType.PTP_DELAY_REQUEST.value:
        response = utils.build_message(utils.PTPMsgType.PTP_DELAY_RESPONSE, arrival_time_ns)
        utils.send_message(sock, response, addr)
        print(f"Sent delay response to {addr}.")
    elif msg_type == utils.PTPMsgType.PTP_SYNC_COMPLETED.value:
        print(f"Sync completed for client {addr}.")
        utils.clear_error_queue(sock)  # Clear error queue after sync completion
        busy = False
        actual_client = None
    else:
        print(f"Unknown message type: {msg_type}.")
    return True

def run_server():
    """
    Run the UDP server to listen for PTP messages with kernel timestamping.
    """
    sock = create_server_socket()
    print(f"Server listening on {IP}:{PORT} with SO_TIMESTAMPING enabled")

    global busy, actual_client
    try:
        tries_count = 0
        while True:
            try:
                data, addr, arrival_time_ns = receive_with_timestamp(sock)
                if len(data) == utils.MSG_SIZE:
                    handle_message(data, addr, sock, arrival_time_ns)
                else:
                    print(f"Received invalid message size from {addr}: {len(data)} bytes.")                
            except socket.error as e:
                tries_count += 1
                if tries_count >= utils.MAX_WAIT_TRIES and busy:
                    print("Client did not respond, freeing server for new connections.")
                    busy = False
                    actual_client = None
                    tries_count = 0
                continue
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        sock.close()
        
if __name__ == "__main__":
    run_server()