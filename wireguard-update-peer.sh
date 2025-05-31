#!/bin/bash

# 检查WireGuard接口状态
interface="wg0"

status=$(ip link show wg0 2>/dev/null)

# 接口状态为 UP 时更新
if [[ "$status" == *"UP"* ]]; then
    sh /usr/share/wireguard-tools/examples/reresolve-dns/reresolve-dns.sh wg0
    echo done
fi