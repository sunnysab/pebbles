import json
import subprocess


def get_current_ip(interface: str) -> list[str]:
    """Get the current IP address of a network interface."""
    result = subprocess.run(['ip', '-4', '-j', 'addr', 'show', interface], capture_output=True, text=True, check=True)
    ifconfig = json.loads(result.stdout)[0]

    ip_address = [x['local'] for x in ifconfig['addr_info']]
    return ip_address


def delete_ip_address(interface: str, ip: str) -> bool:
    """Delete an IP address from a network interface."""
    try:
        subprocess.run(['sudo', 'ip', 'addr', 'del', f'{ip}/24', 'dev', interface], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception as e:
        raise f"An error occurred: {e}"


def add_gateway(gateway: str) -> bool:
    """Add a gateway to the network."""
    try:
        """sudo ip route add 210.35.66.10 via 10.1.160.254"""
        subprocess.run(['sudo', 'ip', 'route', 'add', '210.35.66.10', 'via', gateway], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception as e:
        raise f"An error occurred: {e}"


def add_ip_address(interface: str, ip: str) -> bool:
    """Add an IP address to a network interface."""
    try:
        subprocess.run(['sudo', 'ip', 'addr', 'add', f'{ip}/24', 'dev', interface], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception as e:
        raise f"An error occurred: {e}"


def change_ip_address(interface: str, new_ip: str):
    """Change the IP address of a network interface."""

    current_address_list = get_current_ip(interface)
    for current_address in current_address_list:
        _ = delete_ip_address(interface, current_address)
    add_ip_address(interface, new_ip)
    add_gateway('10.1.160.254')


if __name__ == '__main__':
    print(get_current_ip('eth0'))

    new_ip = input().strip()
    print(change_ip_address('eth0', new_ip))
