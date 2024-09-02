import json
import subprocess


def _run_command(command: str) -> str | None:
    """Run a command and return the output."""
    try:
        result = subprocess.run(command.split(), capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return None
    except Exception as e:
        raise f"An error occurred: {e}"

def get_current_ip(interface: str) -> list[str]:
    """Get the current IP address of a network interface."""
    result = _run_command(f'ip -j -4 addr show {interface}')
    ifconfig = json.loads(result)[0]

    ip_address = [x['local'] for x in ifconfig['addr_info']]
    return ip_address

def delete_ip_address(interface: str, ip: str) -> bool:
    """Delete an IP address from a network interface."""
    return _run_command(f'sudo ip addr del {ip}/24 dev {interface}') is not None

def add_gateway(target: str, gateway: str) -> bool:
    """Add a gateway to the network."""
    return _run_command(f'sudo ip route add {target} via {gateway}') is not None

def add_ip_address(interface: str, ip: str) -> bool:
    """Add an IP address to a network interface."""
    return _run_command(f'sudo ip addr add {ip}/24 dev {interface}') is not None

def change_ip_address(interface: str, new_ip: str):
    """Change the IP address of a network interface."""
    current_address_list = get_current_ip(interface)
    for current_address in current_address_list:
        _ = delete_ip_address(interface, current_address)

    add_ip_address(interface, new_ip)
    add_gateway('210.35.66.10', '10.1.160.254')

if not get_current_ip('eth0'):
    from scan import chose_one

    new_ip = chose_one('eth0', '10.1.160.0/24')
    add_ip_address('eth0', new_ip)
    add_gateway('210.35.66.10', '10.1.160.254')


if __name__ == '__main__':
    print(get_current_ip('eth0'))

    new_ip = input().strip()
    print(change_ip_address('eth0', new_ip))
