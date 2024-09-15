import asyncpg
from typing import List
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Bathroom:
    bathroom_id: int
    area_name: str

@dataclass
class Device:
    device_id: int
    bathroom_id: int
    device_name: str

@dataclass
class StatusChange:
    timestamp: datetime
    device_id: int
    status: str

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

    async def upsert_bathrooms_and_devices(self, bathrooms: List[Bathroom], devices: List[Device]):
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

    async def insert_status_changes(self, status_changes: List[StatusChange]):
        async with self.pool.acquire() as conn:
            await conn.executemany('''
                INSERT INTO status_change (timestamp, device_id, status)
                VALUES ($1, $2, $3)
            ''', [(sc.timestamp.astimezone(timezone.utc), sc.device_id, sc.status) for sc in status_changes])

# 使用示例
async def main():
    db = Database("postgresql://user:password@localhost/dbname")
    await db.connect()

    try:
        # 更新浴室和设备信息
        bathrooms = [
            Bathroom(1, "山东烟台大学-15号楼A楼-一层"),
            Bathroom(2, "山东烟台大学-15号楼B楼-二层")
        ]
        devices = [
            Device(1, 1, "1号"),
            Device(2, 1, "2号"),
            Device(3, 2, "1号")
        ]
        await db.upsert_bathrooms_and_devices(bathrooms, devices)

        # 插入状态变更
        status_changes = [
            StatusChange(datetime.now(), 1, "open"),
            StatusChange(datetime.now(), 2, "close")
        ]
        await db.insert_status_changes(status_changes)

    finally:
        await db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
