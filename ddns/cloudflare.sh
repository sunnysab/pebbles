readonly CLOUDFLARE_EMAIL='i@sunnysab.cn'
readonly CLOUDFLARE_TOKEN='{cloudflare token}'
readonly CLOUDFLARE_ZONE='{zone}'
readonly DOMAIN='{host}.sunnysab.cn'
readonly RECORD_A_IDENTIFIER='{record_a_id}'
readonly RECORD_AAA_IDENTIFIER='{record_aaaa_id}'
readonly INTERFACE='pppoe-wan'

# $1: dns record identifier
# $2: record value
function send_request() {
    curl --request PATCH \
        --url https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE/dns_records/$1 \
        --header 'Content-Type: application/json' \
        --header "X-Auth-Email: $CLOUDFLARE_EMAIL" \
        --header "X-Auth-Key: $CLOUDFLARE_TOKEN" \
        --data "{
        \"content\": \"$2\",
        \"ttl\": 60
        }"
}


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
    send_request $RECORD_A_IDENTIFIER $CURRENT_IP
    # 更新 IP 存储
    echo $CURRENT_IP > /root/LAST_IP
    # 写入日志
    echo "$(date) IP address on pppoe-WAN changed: $LAST_IP -> $CURRENT_IP" >> DDNS.log
fi

# 更新 AAAA 记录
if [ "$LAST_IP6" != "$CURRENT_IP6" ]
then
    # 更新区域文件
    send_request $RECORD_AAA_IDENTIFIER $CURRENT_IP6
    # 更新 IP 存储
    echo $CURRENT_IP6 > /root/LAST_IP6
    # 写入日志
    echo "$(date) IP address on pppoe-WAN changed: $LAST_IP6 -> $CURRENT_IP6" >> DDNS.log
fi
