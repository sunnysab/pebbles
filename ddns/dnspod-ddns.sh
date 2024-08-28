#!/bin/bash

HOSTS_FILE="ddns_hosts.txt"
DDNS_HISTORY_FILE="ddns_history.txt"
NIC="enp2s0"

DOMAIN_POSTFIX="sunnysab.cn"


if [ -z "$DNSPOD_SECRET_ID" ] || [ -z "$DNSPOD_SECRET_KEY" ]; then
    echo "Please set the DNSPOD_SECRET_ID and DNSPOD_SECRET_KEY variable in the script."
    exit 1
fi

if ! [ -f "$HOSTS_FILE" ]; then
    touch "$HOSTS_FILE"
fi


get_ipv4_address() {
    ip -o -f inet addr show $NIC | awk 'NR==1 {print $4}' | cut -d'/' -f1
}


get_ipv6_address() {
    ip -o -f inet6 addr show $NIC | awk 'NR==1 {print $4}' | cut -d'/' -f1
}


submit_dns_record() {
    local domain=$1
    local record_id=$2
    local value=$3

    token=""
    service="dnspod"
    host="dnspod.tencentcloudapi.com"
    region=""
    action="ModifyDynamicDNS"
    version="2021-03-23"
    algorithm="TC3-HMAC-SHA256"
    timestamp=$(date +%s)
    date=$(date -u -d @$timestamp +"%Y-%m-%d")

    # 构造 payload
    # 注意：dnspod 的接口中，需要把域名拆分成主机名和域名后缀.
    subdomain=$(echo "$domain" | sed "s/\.$DOMAIN_POSTFIX$//")
    payload="{\"Domain\":\"$DOMAIN_POSTFIX\",\"SubDomain\":\"$subdomain\",\"RecordId\":$record_id,\"RecordLine\":\"默认\",\"Value\":\"$value\"}"

    # ************* 步骤 1：拼接规范请求串 *************
    http_request_method="POST"
    canonical_uri="/"
    canonical_querystring=""
    canonical_headers="content-type:application/json; charset=utf-8\nhost:$host\nx-tc-action:$(echo $action | awk '{print tolower($0)}')\n"
    signed_headers="content-type;host;x-tc-action"
    hashed_request_payload=$(echo -n "$payload" | openssl sha256 -hex | awk '{print $2}')
    canonical_request="$http_request_method\n$canonical_uri\n$canonical_querystring\n$canonical_headers\n$signed_headers\n$hashed_request_payload"

    # ************* 步骤 2：拼接待签名字符串 *************
    credential_scope="$date/$service/tc3_request"
    hashed_canonical_request=$(printf "$canonical_request" | openssl sha256 -hex | awk '{print $2}')
    string_to_sign="$algorithm\n$timestamp\n$credential_scope\n$hashed_canonical_request"

    # ************* 步骤 3：计算签名 *************
    secret_date=$(printf "$date" | openssl sha256 -hmac "TC3$DNSPOD_SECRET_KEY" | awk '{print $2}')
    secret_service=$(printf $service | openssl dgst -sha256 -mac hmac -macopt hexkey:"$secret_date" | awk '{print $2}')
    secret_signing=$(printf "tc3_request" | openssl dgst -sha256 -mac hmac -macopt hexkey:"$secret_service" | awk '{print $2}')
    signature=$(printf "$string_to_sign" | openssl dgst -sha256 -mac hmac -macopt hexkey:"$secret_signing" | awk '{print $2}')

    # ************* 步骤 4：拼接 Authorization *************
    authorization="$algorithm Credential=$DNSPOD_SECRET_ID/$credential_scope, SignedHeaders=$signed_headers, Signature=$signature"

    # ************* 步骤 5：构造并发起请求 *************
    curl -s -X POST "https://$host" -d "$payload" -H "Authorization: $authorization" -H "Content-Type: application/json; charset=utf-8" -H "Host: $host" -H "X-TC-Action: $action" -H "X-TC-Timestamp: $timestamp" -H "X-TC-Version: $version" -H "X-TC-Region: $region" -H "X-TC-Token: $token" > /dev/null
}

# hosts 的文件格式：
# 域名 地址类型 地址
# 其中地址类型为 4 或 6，表示 IPv4 或 IPv6 地址
update_host_file() {
    local domain=$1
    local family=$2
    local ip_address=$3

    sed -i "/^$domain $family/d" "$HOSTS_FILE"
    # 添加新的记录
    echo "$domain $family $ip_address" >> "$HOSTS_FILE"
    # 记录历史
    echo "$(date) $domain $ip_address" >> "$DDNS_HISTORY_FILE"
}


query_host_file() {
    local domain=$1
    local family=$2

    # 读取 hosts 文件中的现有 IPv6 地址
    grep "$domain $family" "$HOSTS_FILE" | awk '{print $3}'
}


update_ddns() {
    local domain=$1
    local record_id=$2
    local family=$3

    # 获取当前的 IPv4/v6 地址
    current_ip=$(get_ipv"$family"_address)
    # 读取 hosts 文件中的现有的地址
    last_ip=$(query_host_file "$domain" "$family")

    # 判断是否需要更新
    if [[ "$current_ip" != "$last_ip" ]]; then
        # 更新 DNS 记录
        submit_dns_record "$domain" "$record_id" "$current_ip"
        # 更新 hosts 文件
        update_host_file "$domain" "$family" "$current_ip"
        echo "set $domain ($current_ip)"
    fi
}

update_ddns "services.ytu.sunnysab.cn" "1787292394" "6"