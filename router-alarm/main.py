#! /usr/bin/python3

from xdr5410 import TPLinkRouter, DeviceInfo
from monitor import Monitor, current_time
from alarm import send_alarm
import logging

INTERVAL = 2
KEYWORDS = []

logging.basicConfig(level=logging.INFO)

def on_device_up(device: DeviceInfo):
    logging.info(f'{device.hostname} ({device.mac}) up')
    if any(keyword in device.hostname for keyword in KEYWORDS):
        send_alarm(f'老师来了. {device.hostname} ({device.mac})\n{current_time()}')
    
def on_device_down(device: DeviceInfo):
    logging.info(f'{device.hostname} ({device.mac}) down')
    if any(keyword in device.hostname for keyword in KEYWORDS):
        send_alarm(f'老师走了. {device.hostname} ({device.mac})\n{current_time()}')

if __name__ == '__main__':
    router = TPLinkRouter('http://192.168.129.1/')
    router.login('')
    
    monitor = Monitor(router, interval=INTERVAL)
    monitor.set_on_device_up(on_device_up)
    monitor.set_on_device_down(on_device_down)

    monitor.start()
