import struct

class RDPPacket:
    """
    The RDPPacket class represents a packet used in the Reliable Data Protocol (RDP). 
    This class facilitates the encoding and decoding of RDP packets, as well as the computation of packet checksums. 
    Each RDP packet can have various control flags (e.g., SYN, ACK, RST) and carries data.

    The RDPPacket class is used for encoding and decoding RDP packets. It can be employed in conjunction with the RDPConnection class to facilitate reliable data transfer over a network connection.
    The class allows you to create RDP packets with various control flags and encode them into bytes for transmission. It also provides a method for decoding received bytes back into an RDPPacket object, making it easy to process incoming data.
    Additionally, the class includes a checksum computation method to ensure data integrity during transmission.

    NOTE: NEEDS VARIABLE HEADER LENGTH SUPPORT
          NEEDS PACKET FRAGMENTATION SUPPORT
    """
    # Protocol constants
    MAX_PACKET_SIZE = 1024  # Max packet size (bytes)
    DEFAULT_TIMEOUT = 5     # Default timeout for acknowledgements (seconds)

    def __init__(self, source_port, dest_port, seq_num, ack_num, data=b'', syn=False, ack=False, eack=False, rst=False, nul=False):
        """
        Initialize an RDP packet
        :param source_port: Source port
        :param dest_port: Destination port
        :param seq_num: Sequence number
        :param ack_num: Acknowledgement number
        :param data: Data to be sent
        :param syn: SYN flag
        :param ack: ACK flag
        :param eack: EACK flag
        :param rst: RST flag
        :param nul: NUL flag

        """
        self.source_port = source_port
        self.dest_port = dest_port
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.data = data
        self.syn = syn
        self.ack = ack
        self.eack = eack
        self.rst = rst
        self.nul = nul

    def encode(self):
        """
        Encode the packet into bytes.

        Returns:
            bytes: Encoded packet.
        """
        # Header flags
        flags = 0
        flags |= (self.syn << 3)
        flags |= (self.ack << 2)
        flags |= (self.eack << 1)
        flags |= (self.rst)
        flags |= (self.nul << 4)  # NUL flag shifted to use the 5th bit
        header_length = 9  # Assuming no variable header area
        version = 1

        # Combine version (4 bits), flags (4 bits), and header length (8 bits)
        control_and_version = (version << 12) | (flags << 8) | header_length

        # Compute checksum and ensure it's the correct type
        checksum = self.compute_checksum()

        # debug print for all packet header values before packing (port, seq_num, ack_num, data_length, checksum)
        print(f"source_port: {self.source_port}, type: {type(self.source_port)}")
        print(f"dest_port: {self.dest_port}, type: {type(self.dest_port)}")
        print(f"data length: {len(self.data)}, type: {type(len(self.data))}")
        print(f"seq_num: {self.seq_num}, type: {type(self.seq_num)}")
        print(f"ack_num: {self.ack_num}, type: {type(self.ack_num)}")
        print(f"checksum: {checksum}, type: {type(checksum)}")
        


        # Pack the header
        header = struct.pack("!HHHIIII", control_and_version, self.source_port, self.dest_port, len(self.data), self.seq_num, self.ack_num, checksum)

        return header + self.data

    
    @staticmethod
    def decode(packet_bytes):
        """
        Decode the packet from bytes.
        :param packet_bytes: Bytes to decode.
        :return: Decoded RDPPacket object.
        """
        # Unpack the first 22 bytes for the header
        control_and_version, source_port, dest_port, data_length, seq_num, ack_num, checksum = struct.unpack("!HHHIIII", packet_bytes[:22])

        # Extract the last 8 bits which contain the flags
        flags = control_and_version & 0xFF

        # Extract individual flags
        syn = (flags >> 3) & 1  # Extract the SYN flag (4th bit from the right)
        ack = (flags >> 2) & 1  # Extract the ACK flag (3rd bit from the right)
        eack = (flags >> 1) & 1  # Extract the EACK flag (2nd bit from the right)
        rst = flags & 1         # Extract the RST flag (1st bit from the right)
        nul = (flags >> 4) & 1  # Extract the NUL flag (5th bit from the right)

        # Extract the data
        data = packet_bytes[22:]

        # Return the decoded RDPPacket
        return RDPPacket(source_port, dest_port, seq_num, ack_num, data, syn, ack, eack, rst, nul)
    
    def compute_checksum(self):
        """
        Compute the checksum of the packet
        :return: Checksum of the packet
        """
        # Compute checksum with pseudo-RFC method 
        checksum = 0

        #debug print statments for struck.pack
        print(f"source_port: {self.source_port}, type: {type(self.source_port)}")
        print(f"dest_port: {self.dest_port}, type: {type(self.dest_port)}")
        print(f"data length: {len(self.data)}, type: {type(len(self.data))}")
        print(f"seq_num: {self.seq_num}, type: {type(self.seq_num)}")
        print(f"ack_num: {self.ack_num}, type: {type(self.ack_num)}")
        
        header_data = struct.pack("!HHHII", self.source_port, self.dest_port, len(self.data), self.seq_num, self.ack_num)
        for i in range(0, len(header_data), 2):
            checksum += int.from_bytes(header_data[i:i+2], byteorder='big')

        for i in range(0, len(self.data), 2):
            checksum += int.from_bytes(self.data[i:i+2], byteorder='big')

        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum = (checksum >> 16) + checksum  # Simulate rotation through carry
        return ~checksum & 0xffff
    
    def __str__(self):
        """
        :return: String representation of the packet for response from server.
        """
        return f"RDPPacket(source_port={self.source_port}, dest_port={self.dest_port}, seq_num={self.seq_num}, ack_num={self.ack_num}, data={self.data}, syn={self.syn}, ack={self.ack}, eack={self.eack}, rst={self.rst}, nul={self.nul})"
