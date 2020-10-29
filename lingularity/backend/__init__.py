import os
import logging

BASE_LANGUAGE_DATA_PATH = f'{os.getcwd()}/.language_data'

# enable logging
logging.basicConfig(filename='logging.txt', level=logging.INFO)
