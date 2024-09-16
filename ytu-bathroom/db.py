import asyncpg
from typing import List
from dataclasses import dataclass
from datetime import datetime
from entity import Bathroom, DeviceStatus


class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            self.dsn,
            command_timeout=60,
            init=lambda conn: conn.execute('SET timezone = "Asia/Shanghai"')
        )

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def upsert_bathrooms_and_devices(self, bathrooms: List[Bathroom], devices: List[DeviceStatus]):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # 更新浴室信息
                await conn.executemany('''
                    INSERT INTO bathroom (id, area_name)
                    VALUES ($1, $2)
                    ON CONFLICT (id) DO UPDATE
                    SET area_name = EXCLUDED.area_name
                ''', [(b.bathroom_id, b.area_name) for b in bathrooms])

                # 更新设备信息
                await conn.executemany('''
                    INSERT INTO device (id, bathroom_id, device_name)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (id) DO UPDATE
                    SET bathroom_id = EXCLUDED.bathroom_id,
                        device_name = EXCLUDED.device_name
                ''', [(d.device_id, d.bathroom_id, d.device_name) for d in devices])

    async def insert_status_changes(self, status_changes: List[DeviceStatus]):
        def map_status(status: int) -> str:
            return 'open' if status == 1 else 'close'

        async with self.pool.acquire() as conn:
            timestamp = datetime.now()
            await conn.executemany('''
                INSERT INTO status_change (timestamp, device_id, status)
                VALUES ($1, $2, $3)
            ''', [(timestamp, sc.device_id, map_status(sc.status)) for sc in status_changes])

