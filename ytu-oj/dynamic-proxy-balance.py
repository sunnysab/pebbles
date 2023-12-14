#! /usr/bin/python

import subprocess
import requests


TEST_URL: int = 'https://google.com/ncr'
TEST_TIMEOUT: int = 5000

# Make ture you have permission to write this file.
NGINX_CONF: str = '/etc/nginx/proxy.conf'


def scan(cidr: str, port: int = 7890) -> list:
    """ Scan the given CIDR for open port. This function depends on masscan."""
    
    process = subprocess.Popen(['/usr/bin/sudo', 'masscan', f'-p{port}', cidr, 
                                '--rate=10000', '--wait=2', '-oL', '/dev/stdout'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret_code = process.wait()
    
    if ret_code != 0:
        raise Exception('masscan failed with exit code {ret_code}')

    '''
    open tcp 7890 10.10.49.49 1702552128
    open tcp 7890 10.10.49.50 1702552128
    open tcp 7890 10.10.49.155 1702552128
    '''
    stdout: bytes = process.stdout.read()
    stdout: str = stdout.decode('utf-8')
    result = []

    for line in stdout.split('\n'):
        colums = line.split(' ')
        if colums[0] == 'open':
            port = int(colums[2])
            ip = colums[3]
            result.append((ip, port))

    return result


def test_proxy(ip: str, port: int, test_url: str = TEST_URL, timeout = TEST_TIMEOUT) -> bool:
    """ Test if the given proxy is working. This function depends on curl."""

    proxy = {
        'https': f'http://{ip}:{port}'
    }

    try:
        response = requests.get(test_url, proxies=proxy, timeout=timeout, allow_redirects=False)
    except:
        return False
    
    # If the proxy is working, there must be a response with any status code.
    return True


def generate_config(proxies: list) -> str:
    """ Generate the config file for clash. """

    proxies.sort()
    proxies = [f'server {ip}:{port};' for ip, port in proxies]
    proxies = '\n'.join(proxies)

    return f'''
        stream {{

            upstream local-proxy {{
                # Proxy upstreams generated by dynamic-proxy-balance.py
                {proxies}
                # End of upstreams
            }}

            server {{
                    listen [::]:7890;
                    proxy_pass local-proxy;
            }}
        }}
    '''


def write_nginx_config(content: str, config: str = NGINX_CONF):
    """ Write the config to the nginx config file. """

    original_content = open(config, 'r').read()
    if original_content == content:
        # No need to write, to protect the SSD.
        return

    with open(config, 'w') as f:
        f.write(content)
        f.flush()


def main() -> None:
    """ Main function. """

    candidates = scan('10.10.0.0/16', 7890)
    proxies = [(ip, port) for ip, port in candidates if test_proxy(ip, port)]

    from pprint import pprint
    print('Scan result')
    pprint(proxies)

    config = generate_config(proxies)
    write_nginx_config(config)


if __name__ == '__main__':
    main()