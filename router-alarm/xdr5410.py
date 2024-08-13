
import requests
import json
import urllib.parse


class DeviceInfo:
    """ 连上路由器的设备信息. """

    def __init__(self, hostname, mac, wifi_mode, device_type, phy_mode, ip, ipv6, up_speed, down_speed, connect_time, rssi):
        self.mac: str = mac
        self.wifi_mode: int = int(wifi_mode)
        self.device_type: int = int(device_type)
        self.phy_mode: int = int(phy_mode)
        self.ip: str = ip
        self.ipv6: str = ipv6
        self.hostname: str = hostname
        # speed in Kbps
        self.up_speed: int = int(up_speed)
        self.down_speed: int = int(down_speed)
        # time in minutes
        self.connect_time = connect_time
        self.rssi: int = int(rssi)

    def __str__(self):
        return f'{self.hostname} ({self.mac}) @ {self.ip} ({self.ipv6})\n'
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, DeviceInfo):
            return False
        return self.mac == value.mac
    
    def __hash__(self) -> int:
        return hash(self.mac)
    
    def _from_dict_(d: dict):
        mac = d.get('mac', '')
        wifi_mode = int(d.get('wifi_mode', '0'))
        device_type = int(d.get('type', '0'))
        phy_mode = int(d.get('phy_mode', '0'))
        ip = d.get('ip', '')
        ipv6 = d.get('ipv6', '')
        hostname = d.get('hostname', '')
        up_speed = int(d.get('up_speed', '0'))
        down_speed = int(d.get('down_speed', '0'))
        connect_time = d.get('connect_time', '0')
        rssi = int(d.get('rssi', '0'))
        return DeviceInfo(hostname, mac, wifi_mode, device_type, phy_mode, ip, ipv6, up_speed, down_speed, connect_time, rssi)


class TPLinkRouter:
    @staticmethod
    def _url_decode_dict(o: any) -> any:
        if isinstance(o, str):
            return urllib.parse.unquote(o)
        if isinstance(o, list):
            return [TPLinkRouter._url_decode_dict(value) for value in o]
        if isinstance(o, dict):
            return {key: TPLinkRouter._url_decode_dict(value) for key, value in o.items()}
        return o

    def __init__(self, base_url: str):
        assert base_url.startswith('http://')
        self.base_url = base_url if base_url.endswith('/') else f'{base_url}/'
        self.stok = ''
        self.password = ''
        self.session = requests.Session()

    def _post(self, url: str, data: any) -> any:
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
        }

        response = self.session.post(url, headers=headers, data=json.dumps(data))
        response_json = response.json()
        if response_json['error_code'] != 0:
            raise Exception(f'code responded: {response_json["error_code"]}.')
        return response_json

    def _org_auth_pwd(clear_text_password: str) -> str:
        """ 从 `web-static/lib/jquery-1.10.1.js` 中提取的加密函数 """
        def security_encode(a: str, b: str, c: str) -> str:
            e = ''
            l = 187
            n = 187
            g = len(a)
            h = len(b)
            k = len(c)
            f = max(g, h)
            for p in range(f):
                n = l = 187
                if p >= g:
                    n = ord(b[p])
                elif p >= h:
                    l = ord(a[p])
                else:
                    l, n = ord(a[p]), ord(b[p])
                e += c[(l ^ n) % k]
            return e
        return security_encode(
            'RDpbLfCPsJZ7fiv',
            clear_text_password,
            'yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW'
        )

    def login(self, password: str = ''):
        """ 登录路由器，获取管理员凭据. 仅第一次登录时需要提供密码. """
        if not password:
            if not self.password:
                raise Exception('password is required.')
            password = self.password
        
        url = f'{self.base_url}'
        data = {'method': 'do', 'login': {'password': TPLinkRouter._org_auth_pwd(password)}}
        
        try:
            response = self._post(url, data)
            self.stok = response['stok']
            self.password = password
        except Exception as e:
            raise Exception(f'failed to login: {e}')
    
    def devices(self) -> list[DeviceInfo]:
        """ 获取当前连接到路由器的设备信息. """
        def to_device_info(d: dict) -> DeviceInfo:
            device_detail = next(iter(d.values()))
            decoded = TPLinkRouter._url_decode_dict(device_detail)
            return DeviceInfo._from_dict_(decoded)
        
        """ 如果由于意外情况导致 stok 过期，自动重新登录 """
        try_count = 2
        while try_count > 0:
            try_count -= 1
            url = f'{self.base_url}/stok={self.stok}/ds'
            data = {
                'hosts_info': {
                    'table': ['host_info','offline_host'],
                    'name': 'cap_host_num'
                },
                'network': {
                    'name': ['iface_mac','lan']
                },
                'hyfi': {
                    'table': ['connected_ext']
                },
                'method': 'get'
            }
            response = self._post(url, data)
            hosts_info = response.get('hosts_info', {}).get('host_info', [])
            if not hosts_info:
                self.login()
                continue

            return [to_device_info(host) for host in hosts_info]
        return []

if __name__ == '__main__':
    base_url = 'http://192.168.129.1'
    router = TPLinkRouter(base_url)
    router.login('xxxxx')
    devices = router.devices()
    print(devices)
