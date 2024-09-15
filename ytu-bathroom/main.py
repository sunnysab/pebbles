import datetime
import time
import httpx
from dataclasses import dataclass
from typing import List, Dict, Any
import asyncio

@dataclass
class Bathroom:
    bathroom_id: int
    """浴室ID"""
    project_id: int
    """学校ID"""
    name: str
    """浴室名称，如：15号楼A楼浴室"""
    area_id: int
    """区域ID"""
    area_name: str
    """区域名称，如：山东烟台大学-15号楼A楼-一层"""
    max_reservation_num: int
    """最大预约人数"""

    def __repr__(self):
        return f"Bathroom({self.name}, Area: {self.area_name}, Max Reservations: {self.max_reservation_num})"

@dataclass
class DeviceStatus:
    bathroom_id: int
    """浴室ID"""
    device_id: int
    """设备ID"""
    device_name: str
    """设备名称，如：1号"""
    is_use: int
    """是否使用中，1表示使用中，0表示空闲"""

    def __hash__(self):
        return self.device_id

    def __eq__(self, other):
        return self.device_id == other.device_id

    def __repr__(self):
        status = "使用中" if self.is_use == 1 else "空闲"
        return f"Device{self.device_id}({self.device_name}, 状态: {status})"


class APIClient:
    BASE_URL = "https://v3-api.china-qzxy.cn"
    
    def __init__(self, account_id: int, login_code: str, project_id: int, user_id: int):
        self.account_id = account_id
        self.login_code = login_code
        self.project_id = project_id
        self.user_id = user_id

    async def _make_request(self, endpoint: str, params: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data["success"] and data["errorCode"] == 0:
                    return data["data"]
                else:
                    raise Exception(f"API请求失败: {data['errorMessage']}")
            else:
                raise Exception(f"请求失败，状态码: {response.status_code}")

    async def fetch_bathrooms(self) -> List[Bathroom]:
        endpoint = "/device/bath/list/area"
        params = {
            "accountId": self.account_id,
            "areaId": "",
            "loginCode": self.login_code,
            "projectId": self.project_id,
            "userId": self.user_id,
        }
        data = await self._make_request(endpoint, params)
        return [Bathroom(
            bathroom_id=bathroom['bathroomId'],
            project_id=bathroom['projectId'],
            name=bathroom['bathroomName'],
            area_id=bathroom['areaId'],
            area_name=bathroom['areaName'],
            max_reservation_num=bathroom['maxReservationNum']
        ) for bathroom in data]

    async def fetch_device_status(self, bathroom_id: int) -> List[DeviceStatus]:
        endpoint = "/device/reservation/bath/rank"
        params = {
            "myRankFlag": 1,
            "accountId": self.account_id,
            "loginCode": self.login_code,
            "bathroomId": bathroom_id,
            "projectId": self.project_id,
            "userId": self.user_id,
        }
        headers = {'config_project': str(self.project_id)}
        data = await self._make_request(endpoint, params, headers)
        return [DeviceStatus(
            bathroom_id=bathroom_id,
            device_id=device['deviceId'],
            device_name=device['deviceName'],
            is_use=device['isUse'],
        ) for device in data["deviceList"]]

class BathroomManager:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.bathrooms = []
        self.last_devices = dict()

    async def get_all_bathrooms(self) -> List[Bathroom]:
        if not self.bathrooms:
            self.bathrooms = await self.api_client.fetch_bathrooms()
            print(f'loaded {len(self.bathrooms)} bathrooms')
        return self.bathrooms
    
    async def get_bathroom_by_id(self, bathroom_id: int) -> Bathroom:
        if not self.bathrooms:
            await self.get_all_bathrooms()

        for bathroom in self.bathrooms:
            if bathroom.bathroom_id == bathroom_id:
                return bathroom
        return None

    async def get_device_status(self, bathroom_id: int) -> List[DeviceStatus]:
        return await self.api_client.fetch_device_status(bathroom_id)

    async def fetch_all_bathroom_devices(self) -> List[DeviceStatus]:
        bathrooms = await self.get_all_bathrooms()

        tasks = [self.get_device_status(bathroom.bathroom_id) for bathroom in bathrooms]
        all_devices = await asyncio.gather(*tasks)
        all_devices = [device for devices in all_devices for device in devices]
        self.last_devices = {device.device_id: device for device in all_devices}
        return all_devices

    async def count(self) -> tuple[int, int]:
        if not self.last_devices:
            await self.fetch_all_bathroom_devices()
        up = sum(1 for device in self.last_devices.values() if device.is_use == 1)
        down = len(self.last_devices) - up
        return up, down
    
    async def devices_up(self) -> List[DeviceStatus]:
        if not self.last_devices:
            await self.fetch_all_bathroom_devices()
        return [device for device in self.last_devices.values() if device.is_use == 1]
    
    async def devices_down(self) -> List[DeviceStatus]:
        if not self.last_devices:
            await self.fetch_all_bathroom_devices()
        return [device for device in self.last_devices.values() if device.is_use == 0]

    async def diff_bathroom_devices(self):
        cached_devices = self.last_devices
        devices = await self.fetch_all_bathroom_devices()
        if not cached_devices:
            return set(), set()

        devices_up = set()
        devices_down = set()
        for device in devices:
            assert device.device_id in cached_devices
            old_status = cached_devices[device.device_id].is_use
            new_status = device.is_use
            if old_status == 0 and new_status == 1:
                devices_up.add(device)
            elif old_status == 1 and new_status == 0:
                devices_down.add(device)
        return devices_up, devices_down

async def main():
    api_client = APIClient(
        account_id=22766,
        login_code="9c44c02821949bea51bdfc2b9b0d917c",
        project_id=415,
        user_id=13118168
    )
    manager = BathroomManager(api_client)
    up, down = await manager.count()
    print(f'当前设备使用中: {up}, 空闲: {down}')

    devices_up = await manager.devices_up()
    print(f'当前使用中的设备（前10个）:')
    for device in devices_up[:10]:
        bathroom = await manager.get_bathroom_by_id(device.bathroom_id)
        print(bathroom)
    
    INTERVAL = 5
    def update_interval():
        global INTERVAL

        current_time = datetime.datetime.now().time()
        if datetime.time(17, 0) <= current_time <= datetime.time(23, 30):
            INTERVAL = 5
        else:
            INTERVAL = 10

    while True:
        start_tick = time.time()
        up, down = await manager.diff_bathroom_devices()
        end_tick = time.time()

        cost = end_tick - start_tick
        print(f"总耗时: {cost:.2f} 秒")
        print(f'up: {len(up)}, down: {len(down)}')
        
        print(f'up: {up}, down: {down}')

        await asyncio.sleep(max(0, INTERVAL - cost))
        update_interval()

if __name__ == "__main__":
    asyncio.run(main())