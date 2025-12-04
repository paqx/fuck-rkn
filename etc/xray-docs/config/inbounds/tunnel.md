# Tunnel (dokodemo-door)

Tunnel (formerly known as dokodemo-door) can listen to several local ports and send all received data to a specified server's port via outbound, achieving port mapping.

## InboundConfigurationObject

```json
{
  "address": "8.8.8.8",
  "port": 53,
  "portMap": {
    "5555": "1.1.1.1:7777",
    "5556": ":8888", // overrides port only
    "5557": "example.com:" // overrides address only
  },
  "network": "tcp",
  "followRedirect": false,
  "userLevel": 0
}
```

`address`: The address to forward traffic to. It can be an IP address, such as `"1.2.3.4"`, or a domain name, such as `"xray.com"`. It is a string type, defaulting to `"localhost"`.

`port`: The specified port of the target address to forward traffic to, ranging from [0, 65535], numeric type. If not filled or 0, it defaults to the listening port.

`portMap`: A map that links local ports to the required remote address/port (if inbound is listening to several ports). If a local port is not included, it is processed according to the `address`/`port` settings.

`network`: `"tcp"` | `"udp"` | `"tcp,udp"`  
The type of network protocol to accept. For example, when specified as `"tcp"`, only TCP traffic is accepted. The default value is `"tcp"`.

`followRedirect`: `true` | `false`  
When set to `true`, dokodemo-door will recognize data forwarded by iptables and forward it to the corresponding target address. Refer to the `tproxy` setting in [Transport Configuration](config/transport.html#sockoptobject).

`userLevel`: number  
The user level, where the connection uses the local policy corresponding to this user level. The `userLevel` value corresponds to the `level` value in the [policy](config/policy.html#policyobject). If unspecified, it defaults to 0.

## Use Cases

The main uses of dokodemo-door are twofold: acting as a transparent proxy and mapping a port.

Sometimes, certain services do not support using forward proxies like Socks5. Using Tun or Tproxy might be overkill, and these services only communicate with a specific IP on a specific port (e.g., iperf, Minecraft server, Wireguard endpoint). In such cases, dokodemo-door can be useful.

Example Config (assuming the default outbound is a valid proxy):

```json
{
  "listen": "127.0.0.1",
  "port": 25565,
  "protocol": "tunnel",
  "settings": {
    "address": "mc.hypixel.net",
    "port": 25565,
    "network": "tcp",
    "followRedirect": false,
    "userLevel": 0
  },
  "tag": "mc"
}
```

At this time, the core will listen to 127.0.0.1:25565 and forward it to mc.hypixel.net:25565 (a Minecraft server) via the default outbound. By connecting to 127.0.0.1:25565 through the Minecraft client, you effectively connect to the Hypixel server via a proxy.

## Transparent Proxy Configuration Example

Please refer to the [TProxy Configuration Tutorial](../../document/level-2/tproxy) for this section.