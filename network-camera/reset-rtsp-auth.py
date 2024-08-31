from unv import *


FILE = 'network-camera/site/cameras.txt'
lines = open(FILE).readlines()

DEVICES = [line.split()[0] for line in lines]


for device in DEVICES:
    ipcam = UnvIPC(device)

    try:
        ipcam.reset_rtsp_auth()
        print(f'Reset RTSP auth for {device}')
    except Exception as e:
        print(f'Failed to reset RTSP auth for {device}: {e}')
        continue
