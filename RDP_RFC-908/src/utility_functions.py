import random
import os


def generate_initial_sequence_number():
    """
    :return: Generate a random initial sequence number
    """
    return random.randint(0, 10000)  

def read_image_as_byte_stream(image_path):
    """
    Read an image file as a byte stream
    :param image_path: Path to the image file
    :return: Byte stream of the image
    """
    with open(image_path, 'rb') as file:
        return file.read()
    