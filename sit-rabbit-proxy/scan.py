import queue
import subprocess


def _run_arp_scan(interface: str, network: str) -> list:
    """Run the arp-scan command, returns a list of (ip, mac) tuples"""
    result = subprocess.run(
        ['sudo', 'arp-scan', '-I', interface, network],
        capture_output=True,
        text=True
    )

    # Parse the output
    output = result.stdout
    lines = output.split('\n')
    devices = []

    for line in lines:
        parts = line.split()
        if len(parts) == 3 and parts[2] == '(Unknown)':
            ip_address = parts[0]
            mac_address = parts[1]
            devices.append((ip_address, mac_address))

    return devices


def _parse_cidr_4(cidr: str) -> tuple[int, int]:
    """ Parse CIDR address range to int range.  """
    ip, mask = cidr.split('/')
    ip = ip.split('.')
    mask = int(mask)
    ip = [int(i) for i in ip]
    ip = (ip[0] << 24) + (ip[1] << 16) + (ip[2] << 8) + ip[3]
    ip_start = ip & ((-1) << (32 - mask))
    ip_end = ip | ((1 << (32 - mask)) - 1)
    return ip_start + 1, ip_end - 1


def _display_ip4(address: int) -> str:
    """ Convert an IPv4 address to human-readable format. """
    return '.'.join(str((address >> i) & 0xff) for i in [24, 16, 8, 0])


def get_all_available_ip(interface: str, network: str) -> list[str]:
    start, end = _parse_cidr_4(network)
    # From 10.1.160.1 to 10.1.160.253
    full_networks: set = {_display_ip4(i) for i in range(start + 1, end - 2)}
    occupied: set = {i[0] for i in _run_arp_scan(interface, network)}

    return list(full_networks - occupied)


_CHOSEN_IP = queue.Queue(120)
_BLACKLIST = set()

def chose_one(interface: str, network: str) -> str | None:
    available = get_all_available_ip(interface, network)

    def not_in_blacklist(ip: str) -> bool:
        return ip not in _BLACKLIST
    def append_blacklist(ip: str) -> bool:
        assert ip not in _BLACKLIST
        _BLACKLIST.add(ip)
        try:
            _CHOSEN_IP.put(ip, block=False)
        except queue.Full:
            _CHOSEN_IP.get(block=False)
            _CHOSEN_IP.put(ip, block=False)
        return True

    for ip in available:
        if not_in_blacklist(ip):
            append_blacklist(ip)
            return ip
    return None


if __name__ == '__main__':
    ip = get_all_available_ip('wlan0', '192.168.129.0/24')
    print(len(ip))

    for i in range(120):
        print(chose_one('wlan0', '192.168.129.0/24'))
