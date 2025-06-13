import utils
import socket
import time

SERVER_IP = '10.255.32.55'
SERVER_PORT = 8888

t1 = None
t2 = None
t3 = None
t4 = None

def create_client_socket():
    """
    Create a UDP client socket.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(utils.SOCKET_TIMEOUT)  # Set a timeout for the socket operations
    return sock

def start_sync(sock: socket.socket, addr: tuple):
    """
    Start the synchronization process with the server.
    """
    for _ in range(utils.MAX_SYNC_TRIES):
        try:
            request = utils.build_message(utils.PTPMsgType.PTP_SYNC_REQUEST, 0)
            # print request size in bytes
            sock.sendto(request, addr)
            print(f"Sent sync request to {addr}")
            
            data, _ = sock.recvfrom(utils.MSG_SIZE)
            arrival_time = utils.get_current_time()

            msg_type, timestamp = utils.parse_message_raw(data)

            if msg_type == utils.PTPMsgType.PTP_BUSY.value:
                print(f"Server is busy, retrying sync request to {addr}...")
                time.sleep(0.5)  # Wait before retrying
                continue
            elif msg_type == utils.PTPMsgType.PTP_SYNC_RESPONSE.value:
                global t1, t2
                t1 = timestamp
                t2 = int(arrival_time * 1e9)
                print(f"Received sync response, t1={t1}, t2={t2}")
                return True
            else:
                print("Aqui")
                print(f"Unexpected message type {msg_type} received from {addr}.")
                return False
            
        except socket.timeout:
            print(f"Sync request timed out, retrying...")
            continue
    print(f"Failed to synchronize with server {addr} after {utils.MAX_SYNC_TRIES} attempts.")
    return False

def send_completed(sock: socket.socket, addr: tuple):
    """
    Send a completion message to the server.
    """
    try:
        request = utils.build_message(utils.PTPMsgType.PTP_SYNC_COMPLETED, 0)
        sock.sendto(request, addr)
        print(f"Sent sync completed message to {addr}")
    except Exception as e:
        print(f"Failed to send sync completed message: {e}")

def run_client() -> bool:
    """
    Run the UDP client to synchronize with the server.
    """
    sock = create_client_socket()
    addr = (SERVER_IP, SERVER_PORT)

    print(f"Client started, attempting to sync with server at {addr}...")
    if not start_sync(sock, addr):
        return
    
    global t1, t2, t3, t4

    offset_list = []
    offset = 0
    delay = 0

    print(f"Client synchronizing with server...")
    
    for _ in range(utils.MAX_SYNC_TRIES):
        try:
            request = utils.build_message(utils.PTPMsgType.PTP_DELAY_REQUEST, int(utils.get_current_time() * 1e9))
            send_time = utils.get_current_time()
            sock.sendto(request, addr)
            print(f"Sent delay request to {addr}")

            data, _ = sock.recvfrom(utils.MSG_SIZE)

            msg_type, timestamp = utils.parse_message_raw(data)

            if msg_type == utils.PTPMsgType.PTP_DELAY_RESPONSE.value:
                t3 = int(send_time * 1e9)
                t4 = timestamp
                print(f"Received delay response, t3={t3}, t4={t4}")
                offset = ((t2 - t1) - (t4 - t3)) / 2
                delay = ((t2 - t1) + (t4 - t3)) / 2
                offset_list.append(offset)
                print(f"Offset calculated: {offset} ns")
            else:
                print(f"Unexpected message type {msg_type} received from {addr}.")
                break

            request = utils.build_message(utils.PTPMsgType.PTP_SYNC_REQUEST, 0)
            sock.sendto(request, addr)
            print(f"Sent sync request to {addr} after delay response")
            
            data, _ = sock.recvfrom(utils.MSG_SIZE)
            arrival_time = utils.get_current_time()

            msg_type, timestamp = utils.parse_message_raw(data)

            if msg_type == utils.PTPMsgType.PTP_SYNC_RESPONSE.value:
                t1 = timestamp
                t2 = int(arrival_time * 1e9)
                print(f"Received sync response, t1={t1}, t2={t2}")
            else:
                print(f"Unexpected message type {msg_type} received after delay response.")
                break

            if t1 + offset + delay - t2 < 1000000:
                print(f"Synchronization successful for client. Offset: {offset} ns, Delay: {delay} ns")
                send_completed(sock, addr)
                return offset

        except socket.timeout:
            print(f"Delay request timed out, retrying...")
            continue

    send_completed(sock, addr)
    return sum(offset_list) / len(offset_list) if offset_list else None

if __name__ == "__main__":
    offset = run_client() # offset is in nanoseconds
    offset_seconds = offset / 1e9 if offset is not None else None

    if offset_seconds is not None:
        print(f"Client synchronization offset: {offset_seconds:.9f} seconds")
        
        with open('offset.txt', 'w') as f:
            f.write(f"{offset_seconds:.9f}\n")
    else:
        print(f"Client failed to synchronize with the server.")
        with open('offset.txt', 'w') as f:
            f.write("Synchronization failed\n")
         