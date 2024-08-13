

from wxpusher import WxPusher
import logging


TOPIC_ID = 0
TOKEN = 'AT_xxxxxxx'

def send_alarm(summary: str, message: str):
    logging.info(f'alarm: {message}')
    WxPusher.send_message(message, topic_ids=[TOPIC_ID], token=TOKEN)
