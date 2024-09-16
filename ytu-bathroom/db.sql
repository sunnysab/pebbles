/*
    浴室表：浴室id, 区域名称（如：山东烟台大学-15号楼A楼-一层）
    设备表：设备id，所属浴室id，设备名称（如：1号）
    状态变更表：时间戳（东八区），设备id，状态（如：开启，关闭）

    枚举类型：状态（开启，关闭）
*/

CREATE TABLE bathroom (
    id INT PRIMARY KEY,
    area_name TEXT NOT NULL
);

CREATE TABLE device (
    id INT PRIMARY KEY,
    bathroom_id INT NOT NULL,
    device_name TEXT NOT NULL,
    FOREIGN KEY (bathroom_id) REFERENCES bathroom(id)
);

CREATE TYPE action_enum AS ENUM ('open', 'close');

CREATE TABLE status_change (
    timestamp TIMESTAMPTZ NOT NULL,
    device_id INT NOT NULL,
    status action_enum NOT NULL,
    FOREIGN KEY (device_id) REFERENCES device(id)
);

DROP VIEW IF EXISTS status_change_view;
CREATE VIEW status_change_view AS
SELECT
    status_change.timestamp,
    bathroom.area_name,
    device.device_name,
    status_change.status
FROM
    status_change, device, bathroom
WHERE
    status_change.device_id = device.id AND
    device.bathroom_id = bathroom.id;