#! /usr/bin/python3

from xdr5410 import TPLinkRouter, DeviceInfo
from monitor import Monitor, current_time
from alarm import send_alarm

INTERVAL = 2
KEYWORDS = []

def on_device_up(device: DeviceInfo):
    if any(keyword in device.hostname for keyword in KEYWORDS):
        send_alarm(f'老师来了. {device.hostname} ({device.mac})\n{current_time()}')
    
def on_device_down(device: DeviceInfo):
    if any(keyword in device.hostname for keyword in KEYWORDS):
        send_alarm(f'老师走了. {device.hostname} ({device.mac})\n{current_time()}')

if __name__ == '__main__':
    router = TPLinkRouter('http://192.168.129.1/')
    router.login('')
    
    monitor = Monitor(router, interval=INTERVAL)
    monitor.set_on_device_up(on_device_up)
    monitor.set_on_device_down(on_device_down)

    monitor.start()
