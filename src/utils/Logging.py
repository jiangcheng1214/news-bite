import logging

logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)


def info(msg):
    logging.info(msg)
