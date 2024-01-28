import socket
from rdp_connection import RDPConnection  
import time

def run_client(server_ip, server_port):
    """
    Runs an RDP client that connects to a specified server and port, waits for the connection to be established,
    sends data, and receives responses.

    Args:
        server_ip (str): The IP address of the server to connect to.
        server_port (int): The port number of the server to connect to.
    """
    # Create a socket for the client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Create an RDP connection instance for the client
    client_connection = RDPConnection(client_socket, (server_ip, server_port), None, server_port)

    # Open the connection (active open)
    open_status = client_connection.open(passive=False, remote_port=server_port)
    print(open_status)

    # Wait for the connection to be established (state to be "OPEN")
    while client_connection.state != 'OPEN':
        #  add a sleep interval to avoid a busy wait
        time.sleep(0.1)

        # Check for incoming packets (like SYN-ACK) and process them
        packet = client_connection.receive_packet()
        if packet:
            client_connection.process_packet(packet)
        

    # Send data to the server after the connection is established
    data_to_send = b"Hello, server!"
    print(f"Sending data: {data_to_send}")
    client_connection.send(data_to_send)

    # Wait for a response
    response = client_connection.receive()
    if response:
        print(f"Received response: {response}")

    # Close the connection
    print(client_connection.close())

run_client("127.0.0.1", 12345)  # Connect to server at 127.0.0.1 on port 12345
