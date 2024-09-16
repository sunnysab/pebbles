from dataclasses import dataclass


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