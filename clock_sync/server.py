import utils
import socket

IP = '0.0.0.0'
PORT = 8888

busy = False
actual_client = None

def create_server_socket():
    """
    Create a UDP server socket.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of the address
    sock.settimeout(utils.SOCKET_TIMEOUT)
    sock.bind((IP, PORT))
    return sock

def handle_message(data: bytes, addr: tuple, sock: socket.socket, arrival_time: float):
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
            sock.sendto(response, addr)
            return
        else:
            print(f"New client {addr} connected.")
            actual_client = addr
            busy = True

    if msg_type == utils.PTPMsgType.PTP_SYNC_REQUEST.value:
        response = utils.build_message(utils.PTPMsgType.PTP_SYNC_RESPONSE, int(utils.get_current_time() * 1e9))
        sock.sendto(response, addr)
        print(f"Sent sync response to {addr}.")
    elif msg_type == utils.PTPMsgType.PTP_DELAY_REQUEST.value:
        response = utils.build_message(utils.PTPMsgType.PTP_DELAY_RESPONSE, int(arrival_time * 1e9))
        sock.sendto(response, addr)
        print(f"Sent delay response to {addr}.")
    elif msg_type == utils.PTPMsgType.PTP_SYNC_COMPLETED.value:
        print(f"Sync completed for client {addr}.")
        busy = False
        actual_client = None
    else:
        print(f"Unknown message type: {msg_type}.")
    return True

def run_server():
    """
    Run the UDP server to listen for PTP messages.
    """
    sock = create_server_socket()
    print(f"Server listening on {IP}:{PORT}")

    global busy, actual_client
    try:
        tries_count = 0
        while True:
            try:
                data, addr = sock.recvfrom(utils.MSG_SIZE)
                arrival_time = utils.get_current_time()
                if len(data) == utils.MSG_SIZE:
                    handle_message(data, addr, sock, arrival_time)
                else:
                    print(f"Received invalid message size from {addr}: {len(data)} bytes.")
            except socket.timeout:
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