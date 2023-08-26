readonly URL='https://{server}/dns/zone/{domain}/record/host.@/a'
readonly URL6='https://{server}/dns/zone/{domain}/record/host.@/aaaa'
readonly KEY='{your key}'
readonly INTERFACE='pppoe-wan'

# 获取上一次的 IP 地址
if [ -e /root/LAST_IP ]
then
LAST_IP=$(cat LAST_IP)
else
LAST_IP=''
fi

# 获取上一次的 IPv6 地址
if [ -e /root/LAST_IP6 ]
then
LAST_IP6=$(cat LAST_IP6)
else
LAST_IP6=''
fi

# 获取当前的 IP 地址
CURRENT_IP=$(ip addr show $INTERFACE | grep 'inet ' | awk '{print $2}')
CURRENT_IP6=$(ip addr show $INTERFACE | grep 'inet6 ' | awk '{print $2}' | head -n 1)
CURRENT_IP6=${CURRENT_IP6%???}

# 更新 A 记录
if [ "$LAST_IP" != "$CURRENT_IP" ]
then
    # 更新区域文件
    curl -s $URL -X PUT -H "Authorization: Basic $KEY" -H "Content-Type: application/json" -d \{\"values\":\[\"$CURRENT_IP\"\],\"ttl\":60\}
    # 更新 IP 存储
    echo $CURRENT_IP > /root/LAST_IP
    # 写入日志
    echo "$(date) IP address on pppoe-WAN changed: $LAST_IP -> $CURRENT_IP" >> DDNS.log
fi

# 更新 AAAA 记录
if [ "$LAST_IP6" != "$CURRENT_IP6" ]
then
    # 更新区域文件
    curl -s $URL6 -X PUT -H "Authorization: Basic $KEY" -H "Content-Type: application/json" -d \{\"values\":\[\"$CURRENT_IP6\"\],\"ttl\":60\}
    # 更新 IP 存储
    echo $CURRENT_IP6 > /root/LAST_IP6
    # 写入日志
    echo "$(date) IP address on pppoe-WAN changed: $LAST_IP6 -> $CURRENT_IP6" >> DDNS.log
fi
