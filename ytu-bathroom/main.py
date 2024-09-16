import os
import json
import datetime
import time
import httpx
import asyncio
import hashlib
from typing import List, Dict, Any
from db import Database
from entity import Bathroom, DeviceStatus


class APIClient:
    BASE_URL = "https://v3-api.china-qzxy.cn"
    
    def __init__(self):
        self.client = httpx.AsyncClient()

        # 学校相关的账号信息
        self.account_id = None
        # 登录信息（一个hash token）
        self.login_code = None
        # 用户ID
        self.user_id = None
        # 学校ID
        self.project_id = None

        self.login_status = self.load_login_cache()

    def save_login_cache(self):
        with open("login_cache.json", "w") as f:
            json.dump({
                "account_id": self.account_id,
                "login_code": self.login_code,
                "user_id": self.user_id,
                "project_id": self.project_id
            }, f)

    def load_login_cache(self) -> bool:
        if os.path.exists("login_cache.json"):
            with open("login_cache.json", "r") as f:
                data = json.load(f)
                self.account_id = data["account_id"]
                self.login_code = data["login_code"]
                self.user_id = data["user_id"]
                self.project_id = data["project_id"]
                return True
        return False

    async def _make_request(self, endpoint: str, params: Dict[str, Any], headers: Dict[str, str] = None, method: str = "GET") -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        response = await self.client.request(method, url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["success"] and data["errorCode"] == 0:
                return data["data"]
            else:
                raise Exception(f"API请求失败: {data['errorMessage']}")
        else:
            raise Exception(f"请求失败，状态码: {response.status_code}")
        
    async def login(self, phone: str, password: str):
        if self.login_status:
            print("已登录，跳过登录")
            return

        endpoint = "/user/login"
        md5_password = hashlib.md5(password.encode()).hexdigest().upper()[-10:]
        params = {
            "identifier": "",
            "password": md5_password,
            "phoneSystem": "android",
            "telephone": phone,
            "type": 0,
        }
        
        data = await self._make_request(endpoint, params, method="POST")
        
        if not data.get("loginCode") or not data.get("userId"):
            raise Exception("登录失败：未获取到必要信息")
        
        self.login_code = data["loginCode"]
        self.user_id = data["userId"]
        if 'userAccount' in data:
            self.account_id = data['userAccount']['accountId']
            self.project_id = data['userAccount']['projectId']
        else:
            raise Exception("登录成功，但未绑定学校")
        
        self.login_status = True
        self.save_login_cache()

    def login_status(self) -> bool:
        return self.login_status

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

        devices_up, devices_down = set(), set()
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
    from config import QZXY_USER, QZXY_PASSWORD
    from config import DATABASE_URI

    api_client = APIClient()
    await api_client.login(QZXY_USER, QZXY_PASSWORD)
    
    manager = BathroomManager(api_client)
    bathrooms = await manager.get_all_bathrooms()
    devices = await manager.fetch_all_bathroom_devices()

    up, down = await manager.count()
    print(f'当前设备使用中: {up}, 空闲: {down}')

    db = Database(DATABASE_URI)
    await db.connect()
    await db.upsert_bathrooms_and_devices(bathrooms, devices)

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
        
        asyncio.create_task(db.insert_status_changes(up))
        asyncio.create_task(db.insert_status_changes(down))
        end_tick = time.time()

        cost = end_tick - start_tick
        print(f'up: {len(up)}, down: {len(down)}, cost: {cost:.2f}s')

        await asyncio.sleep(max(0, INTERVAL - cost))
        update_interval()

if __name__ == "__main__":
    asyncio.run(main())