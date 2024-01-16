import socket
from rdp_connection import RDPConnection  

def run_server(local_port):
    """
    Runs an RDP server that listens on a specified port, accepts connections, and processes incoming data.

    Args:
        local_port (int): The local port number on which the server listens for incoming connections.
    """
    # Create a socket for the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Create an RDP connection instance for the server
    server_connection = RDPConnection(server_socket, None, local_port, None)

    # Bind the socket to the local port and start listening
    print(server_connection.listen(local_port))

    print("Server is listening for incoming connections...")

    while True:
        # Receive a packet
        packet = server_connection.receive_packet()
        if packet:
            # Process the packet
            response = server_connection.process_packet(packet)

            # Check if there is data to send back
            if response and response.data:
                server_connection.send(response.data)

run_server(12345)  # Run the server on port 12345
