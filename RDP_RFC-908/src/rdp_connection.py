from utility_functions import *
from rdp_protocol import RDPPacket
import socket

class RDPConnection:

    def __init__(self, socket, remote_address, source_port, dest_port):
        """
        Initialize connection parameters.

        - socket: The socket object used for network communication.
        - remote_address: The address of the remote peer (IP, port).
        - state: Current state of the connection (e.g., CLOSED, LISTEN, OPEN).
        - SND_ISS, SND_NXT, SND_UNA: Variables for tracking sequence numbers for sent data.
        - RCV_CUR, RCV_MAX: Variables for tracking sequence numbers for received data.
        - data_buffer: Buffer to temporarily store received data.
        - source_port, dest_port: Local and remote port numbrs.
        """
        self.socket = socket
        self.remote_address = remote_address
        self.state = 'CLOSED'
        self.SND_ISS = 0  # Initial Send Sequence
        self.SND_NXT = 0  # Next Send Sequence
        self.SND_UNA = 0  # Unacknowledged Send Sequence
        self.RCV_CUR = 0  # Current Receive Sequence
        self.RCV_MAX = 0  # Maximum Receive Sequence
        self.data_buffer = b''  # Buffer to store received data
        self.source_port = source_port  # Set this as needed
        self.dest_port = dest_port  # Set this as needed
    
    
    def open(self, passive, local_port=None, remote_port=None, snd_max=None, rmax_buf=None):
        """
        Opens a new connection. It can be passive (server-side) or active (client-side).
        Initializes sequence numbers and sets the state of the connection.
        Args:
            passive (bool): Whether to open the connection in passive mode (server-side).
            local_port (int): The local port to open the connection on.
            remote_port (int): The remote port to connect to.
            snd_max (int): The maximum segment size for sending data.
            rmax_buf (int): The maximum buffer size for receiving data.
        """
        if self.state != 'CLOSED':
            return "Error - connection already open"

        # Generate SND.ISS and initialize SND.NXT and SND.UNA
        self.SND_ISS = generate_initial_sequence_number()
        self.SND_NXT = self.SND_ISS + 1
        self.SND_UNA = self.SND_ISS

        # Set SND.MAX and RMAX.BUF from parameters
        self.SND_MAX = snd_max if snd_max is not None else 10  # Default value
        self.RMAX_BUF = rmax_buf if rmax_buf is not None else 1024  # Default value

        if passive:
            if local_port is None:
                return "Error - local port not specified"
            self.state = 'LISTEN'
            # Additional setup for passive open...
        else:
            if remote_port is None:
                return "Error - remote port not specified"
            if local_port is None:
                local_port = self.allocate_local_port()  # Assuming a method to allocate local port
            self.state = 'SYN-SENT'
            # Send SYN packet with SND.ISS, SND.MAX, RMAX.BUF
            syn_packet = RDPPacket(self.source_port, remote_port, self.SND_ISS, 0, syn=True)
            self.send_packet(syn_packet)

        return f"Connection opened in state {self.state}"


    def close(self):
        """
        Closes the connection.
        Sends a reset packet if necessary and updates the connection state.

        """

        if self.state in ['LISTEN', 'SYN-RCVD', 'SYN-SENT']:
            self.send_rst()
            self.state = 'CLOSED'
            # Additional cleanup...
            return "Connection closed from state: LISTEN/SYN-RCVD/SYN-SENT"

        elif self.state == 'OPEN':
            self.send_rst()
            self.state = 'CLOSE-WAIT'
            # Start TIMWAIT timer...
            # Additional cleanup...
            return "Connection set to CLOSE-WAIT from state: OPEN"

        else:
            return "Error - connection not open or already closing"
        
    def send(self, data):
        """
        Sends data over the connection.
        Args:
            data (bytes): The data to be sent over the connection.
        """
        if self.state != 'OPEN':
            return "Error - connection not open"

        # Check if data size exceeds the maximum segment size
        if len(data) > self.SND_MAX:
            return "Error - data size exceeds maximum segment size"

        # Check if the send window is full
        if self.SND_NXT >= self.SND_UNA + self.SND_MAX:
            return "Error - send window is full, cannot send more data"

        # Prepare and send the data packet
        packet = self.prepare_data_packet(data)
        self.send_packet(packet)

        # Update SND.NXT
        self.SND_NXT += len(data)

    def send_packet(self, packet):
        """ Sends a packet to the remote address. 
        Args:
            packet (RDPPacket): The packet to be sent.
        """
        encoded_packet = packet.encode()
        self.socket.sendto(encoded_packet, self.remote_address)

    def receive_packet(self):
        """ 
        Receives a packet. 
        Returns:
            RDPPacket: The received packet.
        """
        packet_bytes, addr = self.socket.recvfrom(1024)
        if addr != self.remote_address:
            return None  # Ignore packets from unexpected sources
        return RDPPacket.decode(packet_bytes)

    def send_ack(self, remote_port):
        """
        Sends an ACK packet.
        Args:
            remote_port (int): The remote port to send the ACK packet to.
        """
        ack_packet = RDPPacket(self.source_port, remote_port, self.SND_NXT, self.RCV_CUR, ack=True)
        self.send_packet(ack_packet)

    def send_syn_ack(self, remote_port):
        """
        Sends a SYN-ACK packet in response to a received SYN packet.
        Args:
            remote_port (int): The remote port to send the SYN-ACK packet to.
        """
        syn_ack_packet = RDPPacket(self.source_port, remote_port, self.SND_ISS, self.RCV_CUR, syn=True, ack=True)
        self.send_packet(syn_ack_packet)

    def prepare_data_packet(self, data):
        """
        Prepares a data packet for transmission.
        Args:
            data (bytes): The data to be sent in the packet.

        Returns:
            RDPPacket: A packet ready for transmission.
        """
        # Use the next sequence number for this packet
        seq_num = self.SND_NXT

        # The acknowledgement number is the current receive sequence number
        ack_num = self.RCV_CUR

        # Assuming source_port and dest_port are attributes of the RDPConnection
        source_port = self.source_port
        dest_port = self.dest_port

        # Create the packet with the specified source/dest ports, sequence number, acknowledgement number, and data
        # No control flags (SYN, ACK, etc.) are set for a regular data packet
        packet = RDPPacket(source_port, dest_port, seq_num, ack_num, data)

        return packet


    def receive(self):
        """
        Receives data from the connection.
        Returns:
            bytes: The received data.
        """
        if self.state != 'OPEN':
            return "Error - connection not open"

        # Check if there are any packets to process
        incoming_packet = self.receive_packet()  # Assuming a method to receive a packet
        if not incoming_packet:
            return "No data to receive"

        # Process the incoming packet
        self.process_packet(incoming_packet)

        # Assuming the data is stored in a buffer after processing
        if self.data_buffer:
            data = self.data_buffer
            self.data_buffer = b''  # Clear the buffer after reading
            return data
        else:
            return "No new data received"

    def process_packet(self, packet):
        """
        Processes an incoming packet.
        - Checks the packet type and processes it accordingly.
        - Updates the connection state if necessary.
        - Sends a response packet if necessary through handle functions.
        Args:
            packet (RDPPacket): The packet to be processed.

        """

        #debug print
        print(f"Processing packet: {packet}")
        # Decode the packet
        decoded_packet = packet.decode()

        # Handle packets based on the current state
        if self.state == 'LISTEN':
            if decoded_packet.syn and not decoded_packet.ack:
                # Process SYN packet
                self.handle_syn_packet(decoded_packet)
            # Handle other packet types if needed

        elif self.state == 'SYN-SENT':
            if decoded_packet.syn and decoded_packet.ack:
                # Process SYN-ACK packet
                self.handle_syn_ack_packet(decoded_packet)
            # Handle other packet types if needed

        elif self.state == 'SYN-RCVD':
            if decoded_packet.ack:
                # Process ACK packet
                self.handle_ack_packet(decoded_packet)
            # Handle other packet types if needed

        elif self.state == 'OPEN':
            if decoded_packet.data:
                # Process DATA packet
                self.handle_data_packet(decoded_packet)
            elif decoded_packet.rst:
                # Process RST packet
                self.handle_rst_packet(decoded_packet)
            # Handle other packet types if needed
        return RDPPacket(self.source_port, self.dest_port, self.SND_NXT, self.RCV_CUR, b"Test response")

            
    def handle_syn_packet(self, packet):
        """
        Handles a received SYN packet.
        Args:
            packet (RDPPacket): The received SYN packet.
        """
        # This is a basic logic example, it should be expanded as per protocol requirements
        if self.state == 'LISTEN' and packet.syn:
            self.RCV_CUR = packet.seq_num
            self.send_syn_ack(packet.source_port)  # Assuming this method sends a SYN-ACK response
            self.state = 'SYN-RCVD'

    def handle_syn_ack_packet(self, packet):
        """
        Handles a received SYN-ACK packet.
        Args:
            packet (RDPPacket): The received SYN-ACK packet.
        """
        # For SYN-SENT state receiving SYN-ACK
        if self.state == 'SYN-SENT' and packet.syn and packet.ack:
            self.RCV_CUR = packet.seq_num
            self.send_ack(packet.source_port)  # Send ACK to complete three-way handshake
            self.state = 'OPEN'

    def handle_ack_packet(self, packet):
        """
        Handles a received ACK packet.
        Args:
            packet (RDPPacket): The received ACK packet.
        """
        # For SYN-RCVD state receiving ACK
        if self.state == 'SYN-RCVD' and packet.ack:
            self.state = 'OPEN'

    def handle_data_packet(self, packet):
        """
        Handles a received DATA packet.
        Args:
            packet (RDPPacket): The received DATA packet.
        """
        # For OPEN state receiving DATA
        if self.state == 'OPEN' and packet.data:
            # Store or process data
            self.data_buffer += packet.data
            self.send_ack(packet.source_port)  # Send ACK for received data

    def handle_rst_packet(self, packet):
        """
        Handles a received RST packet.
        Args:
            packet (RDPPacket): The received RST packet.
        """
        # For OPEN state receiving RST
        if self.state == 'OPEN' and packet.rst:
            self.state = 'CLOSED'
            self.reset_connection()  # Reset the connection parameters

    def send_rst(self):
        """
        Sends a reset packet.
        """
        # send RST (reset) packet
        rst_packet = RDPPacket(self.source_port, self.dest_port, self.SND_NXT, self.RCV_CUR, rst=True)
        self.send_packet(rst_packet)  # Assuming send_packet method sends the packet

    def listen(self, local_port):
        """
        Listens for incoming connections.
        Args:
            local_port (int): The local port to listen on.
        """
        try:
            self.socket.bind(('', local_port))
            self.local_port = local_port
            self.state = 'LISTEN'
            return "Listening on port " + str(local_port)
        except socket.error as e:
            return f"Error binding to port {local_port}: {e}"


    def handle_state_transition(self, current_state, event):

        """
        Handles a state transition.
        Args:
            current_state (str): The current state of the connection.
            event (str): The event that triggered the transition.
        """
        if current_state == 'LISTEN':
            if event == 'RECEIVE_SYN':
                # Process SYN packet and send SYN-ACK
                self.state = 'SYN-RCVD'
            # Other conditions...

        elif current_state == 'SYN-SENT':
            if event == 'RECEIVE_SYN_ACK':
                # Process SYN-ACK packet
                self.state = 'OPEN'
            # Other conditions...

        elif current_state == 'SYN-RCVD':
            if event == 'RECEIVE_ACK':
                # Process ACK
                self.state = 'OPEN'
            # Other conditions...

        # Add more states and their transitions as needed

        return "Transitioned to state " + self.state
    
    def reset_connection(self):
        """
        Resets the connection parameters.
        """
        self.state = 'CLOSED'
        self.SND_ISS = self.SND_NXT = self.SND_UNA = 0
        self.RCV_CUR = self.RCV_MAX = 0
        self.data_buffer = b''

    def allocate_local_port(self):
        """
            Allocates a local port for the connection.
        """
        # allocate a local port
        self.source_port = 10000  
        return self.source_port
        

