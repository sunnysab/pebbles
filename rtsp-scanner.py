#! /usr/bin/env python

import cv2


CIDR = '192.168.3.0/24'

def parse_cidr_4(cidr: str) -> tuple[int, int]:
    """ Parse CIDR address range to int range.  """
    ip, mask = cidr.split('/')
    ip = ip.split('.')
    mask = int(mask)
    ip = [int(i) for i in ip]
    ip = (ip[0] << 24) + (ip[1] << 16) + (ip[2] << 8) + ip[3]
    ip_start = ip & ((-1) << (32 - mask))
    ip_end = ip | ((1 << (32 - mask)) - 1)
    return ip_start, ip_end


def display_ip4(address: int) -> str:
    """ Convert an IPv4 address to human-readable format. """
    return '.'.join(str((address >> i) & 0xff) for i in [24, 16, 8, 0])


def show_rtsp(title: str, source: str) -> bool:
    """ Show RTSP stream using OpenCV. If user presses 'q', break.
     
    Returns:
        bool: True if user pressed 'q', False otherwise.
    """
    cap = cv2.VideoCapture(source)
    if cap.isOpened() is False:
        print('Error opening video stream or file')
        return False
    
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, 1280, 720)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow(title, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return True


start, end = parse_cidr_4(CIDR)
for i in range(start, end):
    ip = display_ip4(i)
    rtsp = f'rtsp://admin:admin@{ip}:554'
    print(rtsp)
    show_rtsp(ip, rtsp)
    