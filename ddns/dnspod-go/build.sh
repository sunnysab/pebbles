#!/bin/sh

GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" dnspod.go
scp ./dnspod root@openwrt:/root/