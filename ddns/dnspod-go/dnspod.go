package main

import (
	"fmt"
	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common"
	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common/errors"
	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common/profile"
	dnspod "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/dnspod/v20210323"
	"net"
	"os"
)

const Interface = "pppoe-wan"
const SecretId = "secret id"
const SecretKey = "secret key"

func RequestToDnspod(client *dnspod.Client, request *dnspod.ModifyDynamicDNSRequest) (err error) {
	_, err = client.ModifyDynamicDNS(request)
	if _, ok := err.(*errors.TencentCloudSDKError); ok {
		fmt.Printf("An API error has returned: %s", err)
		return
	}
	return
}

func UpdateAddr4(client *dnspod.Client, addr string) (err error) {
	request := dnspod.NewModifyDynamicDNSRequest()
	request.Domain = common.StringPtr("sunnysab.cn")
	request.SubDomain = common.StringPtr( /* host */ )
	request.RecordId = common.Uint64Ptr( /* record id*/ )
	request.RecordLine = common.StringPtr("默认")
	request.Value = common.StringPtr(addr)

	return RequestToDnspod(client, request)
}

func UpdateAddr6(client *dnspod.Client, addr string) (err error) {
	request := dnspod.NewModifyDynamicDNSRequest()
	request.Domain = common.StringPtr("sunnysab.cn")
	request.SubDomain = common.StringPtr( /* host */ )
	request.RecordId = common.Uint64Ptr( /* record id */ )
	request.RecordLine = common.StringPtr("默认")
	request.Value = common.StringPtr(addr)

	return RequestToDnspod(client, request)
}

type IpAddress struct {
	IpVer   int
	Address string
}

type NetInterface struct {
	Name string
	Addr []IpAddress
}

func GetNetInterface() (iface []NetInterface, err error) {
	interfaces, err := net.Interfaces()
	if err != nil {
		return iface, err
	}

	// https://en.wikipedia.org/wiki/IPv6_address#General_allocation
	_, ipv6Unicast, _ := net.ParseCIDR("2000::/3")

	for i := 0; i < len(interfaces); i++ {
		if (interfaces[i].Flags & net.FlagUp) != 0 {
			addrs, _ := interfaces[i].Addrs()
			addrs_to_save := []IpAddress{}

			for _, address := range addrs {
				if ipnet, ok := address.(*net.IPNet); ok && ipnet.IP.IsGlobalUnicast() {
					_, bits := ipnet.Mask.Size()
					// 匹配全局单播地址
					if bits == 128 && ipv6Unicast.Contains(ipnet.IP) {
						addrs_to_save = append(addrs_to_save, IpAddress{IpVer: 6, Address: ipnet.IP.String()})
					} else if bits == 32 {
						addrs_to_save = append(addrs_to_save, IpAddress{IpVer: 4, Address: ipnet.IP.String()})
					}
				}
			}
			iface = append(iface, NetInterface{Name: interfaces[i].Name, Addr: addrs_to_save})
		}
	}
	return iface, nil
}

func GetAddressByInterface(ifaceName string) (addrs []IpAddress, err error) {
	pairs, err := GetNetInterface()
	if err != nil {
		return addrs, err
	}

	for _, iface := range pairs {
		if iface.Name == ifaceName {
			return iface.Addr, nil
		}
	}
	return addrs, nil
}

func ReadLastIp(fileName string) (string, error) {
	content, err := os.ReadFile(fileName)
	if err != nil {
		return "", fmt.Errorf("无法读取文件：%w", err)
	}
	return string(content), err
}

func CacheLastIp(fileName string, addr string) (err error) {
	err = os.WriteFile(fileName, []byte(addr), 0644)
	if err != nil {
		return err
	}
	return
}

func main() {
	addrs, err := GetAddressByInterface(Interface)
	if err != nil {
		fmt.Printf("unable to get address by %s: %s", "wlan0", err.Error())
		return
	}

	credential := common.NewCredential(SecretId, SecretKey)
	cpf := profile.NewClientProfile()
	cpf.HttpProfile.Endpoint = "dnspod.tencentcloudapi.com"
	client, _ := dnspod.NewClient(credential, "", cpf)

	v4, v6 := false, false
	for _, addr := range addrs {
		if !v4 && addr.IpVer == 4 {
			lastV4, err := ReadLastIp("LAST_IP")
			if err != nil {
				lastV4 = ""
			}

			if lastV4 == addr.Address {
				continue
			}
			err = UpdateAddr4(client, addr.Address)
			if err != nil {
				fmt.Errorf("errors when updating v4 addr: %s", err)
			}
			CacheLastIp("LAST_IP", addr.Address)
			v4 = true
		} else if !v6 && addr.IpVer == 6 {
			lastV6, err := ReadLastIp("LAST_IP6")
			if err != nil {
				lastV6 = ""
			}

			if lastV6 == addr.Address {
				continue
			}
			err = UpdateAddr6(client, addr.Address)
			if err != nil {
				fmt.Errorf("errors when updating v6 addr: %s", err)
			}
			CacheLastIp("LAST_IP6", addr.Address)
			v6 = true
		}
	}
}
