# Inbound Proxy

Inbound connections receive incoming data. For available protocols, see [Inbound Protocols](https://example.com/config/inbounds/).

## InboundObject

`InboundObject` corresponds to a sub-element of the `inbounds` item in the configuration file.

```json
{
  "inbounds": [
    {
      "listen": "127.0.0.1",
      "port": 1080,
      "protocol": "protocol name",
      "settings": {},
      "streamSettings": {},
      "tag": "identifier",
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      }
    }
  ]
}
```

- **`listen`: address**  
  Listening address, either an IP address or Unix domain socket. Default is `"0.0.0.0"`, meaning it listens on all network interfaces. Can specify a specific IP address available on the system.

- **`port`: number | "env:variable" | string**  
  Port number. Acceptable formats include:
  - Integer: Actual port number.
  - Environment variable: Starts with `"env:"` followed by a variable name, e.g., `"env:PORT"`.
  - String: A numeric string, e.g., `"1234"`, or a range, e.g., `"5-10"` or `"11,13,15-17"`.

- **`protocol`: "dokodemo-door" | "http" | "shadowsocks" | "socks" | "vless" | "vmess" | "trojan" | "wireguard"**  
  Connection protocol name. A list of available protocols is shown in the inbound proxy section.

- **`settings`: InboundConfigurationObject**  
  Specific configuration content that varies by protocol. See each protocol's `InboundConfigurationObject` for details.

- **`streamSettings`: [StreamSettingsObject](https://example.com/config/transport.html#streamsettingsobject)**  
  The underlying transport method, linking the current Xray node to others.

- **`tag`: string**  
  Identifier for this inbound connection, used for locating it in other configurations.

  > **Warning**  
  > The `tag` must be **unique** among all tags if set.

- **`sniffing`: SniffingObject**  
  Flow detection used mainly for transparent proxy purposes. Sniffs traffic to extract domain names for effective routing.

### SniffingObject

```json
{
  "enabled": true,
  "destOverride": ["http", "tls", "fakedns"],
  "metadataOnly": false,
  "domainsExcluded": [],
  "routeOnly": false
}
```

- **`enabled`: true | false**  
  Whether to enable traffic detection.

- **`destOverride`: ["http" | "tls" | "quic" | "fakedns"]**  
  Resets the target of the current connection based on specified traffic types.

  > **Tip**  
  > To sniff domain names for routing without resetting the target (useful with Tor Browser), add the protocol here and enable `routeOnly`.

- **`metadataOnly`: true | false**  
  Uses connection metadata to detect target addresses. Disables non-`fakedns` sniffers when enabled.

- **`domainsExcluded`: [string]**  
  List of domains where detected results will not reset the target address. Can use direct domain matches or `regexp:` prefixed regular expressions.

  > **Tip**  
  > Add domains here to resolve issues with iOS notifications, smart devices, or game voice chats. For testing, disable `sniffing` or enable `routeOnly`.

- **`routeOnly`: true | false**  
  Use detected domain names solely for routing; the proxy target remains the IP. Default is `false`.

  > **Tip**  
  > When ensuring **correct DNS resolution** of proxied connections, enabling `routeOnly` with `destOverride` and setting `domainStrategy` as `AsIs` achieves domain and IP diversion without DNS resolution.
