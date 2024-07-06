#! /usr/bin/env python3

import time
from typing import Callable
from xdr5410 import TPLinkRouter, DeviceInfo


class Monitor:
    @staticmethod
    def differenate_devices(old_devices: list[DeviceInfo], new_devices: list[DeviceInfo]) \
        -> tuple[list[DeviceInfo], list[DeviceInfo]]:
        """ 比较两次设备信息，返回新增设备和离线设备. """
        old, new = set(old_devices), set(new_devices)
        up = new.difference(old)
        down = old.difference(new)
        return list(up), list(down)

    def __init__(self, router: TPLinkRouter, interval: int = 2):
        self.interval = interval
        self.router = router
        self.error_count = 0
        self.devices = router.devices()
        self.on_device_up: Callable[[DeviceInfo], None] | None = None
        self.on_device_down: Callable[[DeviceInfo], None] | None = None

    def set_on_device_up(self, device_up_callback: Callable[[DeviceInfo], None]):
        self.on_device_up = device_up_callback

    def set_on_device_down(self, device_down_callback: Callable[[DeviceInfo], None]):
        self.on_device_down = device_down_callback

    def get_devices(self) -> list[DeviceInfo]:
        try:
            devices = self.router.devices()
            self.error_count = 0
            return devices
        except Exception as e:
            self.error_count += 1
            print(f'Error: {e}')

    def start(self):
        while True:
            new_devices = self.get_devices()
            up, down = Monitor.differenate_devices(self.devices, new_devices)
            self.devices = new_devices

            for device in up:
                if self.on_device_up:
                    self.on_device_up(device)
            for device in down:
                if self.on_device_down:
                    self.on_device_down(device)
            
            time.sleep(self.interval)


def current_time() -> str:
    return time.strftime(r'%Y-%m-%d %H:%M:%S', time.localtime())
