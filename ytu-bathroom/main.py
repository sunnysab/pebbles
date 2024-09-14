import httpx
from typing import List, Dict, Any
import asyncio

class Bathroom:
    def __init__(self, bathroom_id: int, project_id: int, name: str, area_id: int, area_name: str, max_reservation_num: int):
        self.bathroom_id = bathroom_id
        self.project_id = project_id
        self.name = name
        self.area_id = area_id
        self.area_name = area_name
        self.max_reservation_num = max_reservation_num

    def __repr__(self):
        return f"Bathroom({self.name}, Area: {self.area_name}, Max Reservations: {self.max_reservation_num})"

class DeviceStatus:
    def __init__(self, device_id: int, device_name: str, is_use: int, mac_address: str):
        self.device_id = device_id
        self.device_name = device_name
        self.is_use = is_use
        self.mac_address = mac_address

    def __repr__(self):
        status = "使用中" if self.is_use == 1 else "空闲"
        return f"Device({self.device_name}, 状态: {status}, MAC: {self.mac_address})"

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
            device_id=device['deviceId'],
            device_name=device['deviceName'],
            is_use=device['isUse'],
            mac_address=device['macAddress']
        ) for device in data["deviceList"]]

class BathroomManager:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def get_all_bathrooms(self) -> List[Bathroom]:
        return await self.api_client.fetch_bathrooms()

    async def get_device_status(self, bathroom_id: int) -> List[DeviceStatus]:
        return await self.api_client.fetch_device_status(bathroom_id)

    async def print_bathroom_info(self):
        bathrooms = await self.get_all_bathrooms()
        for bathroom in bathrooms:
            print(f"\n{bathroom}")
            devices = await self.get_device_status(bathroom.bathroom_id)
            for device in devices:
                print(f"  - {device}")

async def main():
    api_client = APIClient(
        account_id=22766,
        login_code="9c44c02821949bea51bdfc2b9b0d917c",
        project_id=415,
        user_id=13118168
    )
    manager = BathroomManager(api_client)
    await manager.print_bathroom_info()

if __name__ == "__main__":
    asyncio.run(main())