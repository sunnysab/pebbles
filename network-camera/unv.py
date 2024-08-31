#!/usr/bin/env python3
import os
import requests
from requests.auth import HTTPDigestAuth


class UnvIPC:
    def __init__(self, host, username='admin', password='admin'):
        self.host = host
        self.base_url = f"http://{host}"
        self.username = username
        self.password = password

        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(self.username, self.password)

    def _request(self, method, url, **kwargs) -> any:
        method_func = None
        match method:
            case 'put': method_func = self.session.put
            case 'post': method_func = self.session.post
            case 'delete': method_func = self.session.delete
            case _: method_func = self.session.get

        response = method_func(url, timeout=1, **kwargs)
        response.raise_for_status()

        response.encoding = 'utf-8'
        json_data = response.json()
        assert 'Response' in json_data, "Invalid response format"

        if json_data["Response"]["ResponseCode"] != 0:
            code, message = json_data["Response"]["ResponseCode"], json_data["Response"]["ResponseString"]
            raise Exception(f"Error: {code} {message}")
        
        return json_data['Response']['Data']
            
    def _put(self, url, **kwargs) -> any:
        self._request('put', url, **kwargs)

    def _get(self, url, **kwargs) -> any:
        self._request('get', url, **kwargs)

    def get_basic_info(self):
        data = self._get(self.base_url + '/LAPI/V1.0/System/DeviceBasicInfo')

        """
        {'Manufacturer': 'UNIVIEW', 
         'DeviceModel': 'IPC-B312-IR@DP-IR3-F60-C', 
         'DeviceConfig': '', 
         'SerialNumber': '210235C2QSA188000194', 
         'MAC': '48ea638b0791', 
         'FirmwareVersion': 'IPC_G6103-B0009P30D1803', 
         'HardewareID': 'A', 
         'PCBVersion': 'A', 
         'UbootVersion': 'V2.0', 
         'CameraVersion': '', 
         'Address': '192.168.3.86', 
         'Netmask': '255.255.255.0', 
         'Gateway': '192.168.3.254'}
        """
        return data
    
    def get_osd_settings(self) -> list[str]:
        data = self._get(self.base_url + '/LAPI/V1.0/Channel/0/Media/OSD/0')
        result = []
        for osd in data['InfoOSD']:
            if osd['Enable'] != 1:
                continue

            for param in osd['InfoParam']:
                if param['InfoType'] == 1:
                    s = param['Value']
                    result.append(s)
        return result
    
    def reset_rtsp_auth(self, mode: int = 1):
        # http://192.168.3.86/LAPI/V1.0/NetWork/RtspAuth
        self._put(self.base_url + '/LAPI/V1.0/NetWork/RtspAuth', json={"Mode": mode})


def parse_serial_number(device_info: dict) -> str:
    return device_info['SerialNumber']


def query_parameter(device: str) -> tuple[str, str]:
    ipcam = UnvIPC(device)
    device_info = ipcam.get_basic_info()
    serial_number = parse_serial_number(device_info)

    osd_settings = ipcam.get_osd_settings()
    osd_text = ';'.join(osd_settings)
    return serial_number, osd_text


def parse_cidr_4(cidr: str) -> tuple[int, int]:
    """ Parse CIDR address range to int range.  """
    ip, mask = cidr.split('/')
    ip = ip.split('.')
    mask = int(mask)
    ip = [int(i) for i in ip]
    ip = (ip[0] << 24) + (ip[1] << 16) + (ip[2] << 8) + ip[3]
    ip_start = ip & ((-1) << (32 - mask))
    ip_end = ip | ((1 << (32 - mask)) - 1)
    return ip_start + 1, ip_end - 1


def display_ip4(address: int) -> str:
    """ Convert an IPv4 address to human-readable format. """
    return '.'.join(str((address >> i) & 0xff) for i in [24, 16, 8, 0])


if __name__ == "__main__":
    NETWORK = '192.168.3.0/24'
    OUTPUT_FILE = 'output.txt'
    MODE = 'a' if os.path.exists(OUTPUT_FILE) else 'w+'

    start, end = parse_cidr_4(NETWORK)
    output_file = open(OUTPUT_FILE, MODE)
    for i in range(start, end):
        ip = display_ip4(i)
        try:
            serial_number, osd_text = query_parameter(ip)
            print(f"{ip}; {serial_number}; {osd_text}")
            output_file.write(f"{ip}\t{serial_number}\t{osd_text}\n")
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            print(f"{ip}; {e}")

    output_file.close()
