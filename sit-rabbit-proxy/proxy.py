from mitmproxy import http
from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster

from ifconfig import change_ip_address
from scan import chose_one

import asyncio


class IpChanger:
    """ mitmproxy addon

    Change the IP address of the network interface when the current IP address is frozen."""
    @staticmethod
    def is_login_request(flow: http.HTTPFlow) -> bool:
        return flow.request.method == 'GET' \
            and flow.request.pretty_host == 'authserver.sit.edu.cn' \
            and flow.request.path == '/authserver/login'

    @staticmethod
    def has_been_freezed(flow: http.HTTPFlow) -> bool:
        return 'IP被冻结' in flow.response.text

    def response(self, flow: http.HTTPFlow):
        if IpChanger.is_login_request(flow) and flow.response.status_code == 200:
            if IpChanger.has_been_freezed(flow):
                new_ip = chose_one('eth0', '10.1.160.0/24')
                change_ip_address('eth0', new_ip)
                print(f'IP changed to {new_ip}')

async def run():
    options = Options(listen_host='0.0.0.0', listen_port=8080, http2=True)
    master = DumpMaster(options, with_termlog=False, with_dumper=False)
    master.addons.add(IpChanger())
    await master.run()


if __name__ == '__main__':
    asyncio.run(run())
