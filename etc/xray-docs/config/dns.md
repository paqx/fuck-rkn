# Built-in DNS Server

## DNS Server

The built-in DNS module of Xray primarily serves three purposes:

- **Resolving domain names to IPs during routing**: This is used for rule matching based on the IP obtained from the domain resolution. Whether the domain is resolved for routing depends on the `domainStrategy` value in the routing configuration module. The built-in DNS server performs DNS queries only when the following values are set:

  - **"IPIfNonMatch"**: When a domain is requested, matching occurs within the routing's domain. If no result is found, the built-in DNS server queries the domain name and attempts IP routing with the returned IP.
  - **"IPOnDemand"**: Resolves the domain into IP immediately upon encountering any IP-based rules during matching.

- **Resolving the target address for connection**:

  - In the `freedom` outbound, when `domainStrategy` is set to `UseIP`, requests are first resolved into IPs via the built-in server and then connected.
  - In `sockopt`, setting `domainStrategy` to `UseIP` enables system connections initiated via outbound to resolve through the built-in server before connecting.

- **Intercepting DNS traffic in transparent proxies** or exposing port 53 directly to act as a recursive DNS server.

> **TIP 1**  
> DNS queries sent by the built-in DNS server are automatically forwarded based on the routing configuration.

> **TIP 2**  
> Only basic IP queries (A and AAAA records) are supported. CNAME records are repeatedly queried until an A/AAAA record is returned. Other queries won't enter the built-in DNS server and can be discarded or pass-through to other servers based on your configuration.

## DNS Processing Flow

If the domain to be queried:

- Matches a "domain-to-IP" or "domain-to-IP array" mapping in `hosts`, the IP or IP array is returned as the DNS resolution result.
- Matches a "domain-to-domain" mapping in `hosts`, the value (another domain) is then queried through the DNS processing flow until an IP is resolved, or an empty result is returned.
- Doesn't match `hosts` but matches a domain list in a DNS server's `domains`, queries are executed sequentially using the corresponding DNS server based on priority. If querying the matched DNS server fails or does not match `expectedIPs`, the next matched DNS server is tried. If all servers fail or `expectedIPs` do not match, the following occurs:

  - **Default DNS Fallback**: Uses an unused DNS server from the previous failed queries, with `skipFallback` defaulting to `false`. If querying fails or `expectedIPs` do not match, an empty result is returned.
  - If `disableFallback` is `true`, no fallback queries are performed.

- Neither matches `hosts` nor a domain list, the DNS component will:

  - **Default**: Utilizes DNS servers with `skipFallback` set to false in sequence. If the first selected server fails or does not match `expectedIPs`, the next server is tried. If all selected DNS servers fail or do not match `expectedIPs`, an empty result is returned.
  - If no server with `skipFallback` set to false exists or `disableFallback` is `true`, the first DNS server in the configuration is used. Failure or non-matching results in an empty resolution.

## DnsObject

`DnsObject` corresponds to the `dns` item in the configuration file.

```json
{
  "dns": {
    "hosts": {
      "baidu.com": "127.0.0.1",
      "dns.google": ["8.8.8.8", "8.8.4.4"]
    },
    "servers": [
      "8.8.8.8",
      "8.8.4.4",
      {
        "address": "1.2.3.4",
        "port": 5353,
        "domains": ["domain:xray.com"],
        "expectedIPs": ["geoip:cn"],
        "skipFallback": false,
        "clientIP": "1.2.3.4"
      },
      {
        "address": "https://8.8.8.8/dns-query",
        "domains": ["geosite:netflix"],
        "skipFallback": true,
        "queryStrategy": "UseIPv4"
      },
      {
        "address": "https://1.1.1.1/dns-query",
        "domains": ["geosite:openai"],
        "skipFallback": true,
        "queryStrategy": "UseIPv6"
      },
      "localhost"
    ],
    "clientIp": "1.2.3.4",
    "queryStrategy": "UseIP",
    "disableCache": false,
    "disableFallback": false,
    "disableFallbackIfMatch": false,
    "useSystemHosts": false,
    "tag": "dns_inbound"
  }
}
```

> **TIP 1**  
> When using `localhost`, local DNS requests are outside Xray control and require additional configuration for routing through Xray.

> **TIP 2**  
> The DNS client initialization is logged as `info` during startup, showing modes such as `local DOH`, `remote DOH`, and `udp`.

> **TIP 3**  
> (v1.4.0+) You can enable DNS query logs in [logging configuration](https://example.com/config/log.html).

### DnsServerObject

```json
{
  "tag": "dns-tag",
  "address": "1.2.3.4",
  "port": 5353,
  "domains": ["domain:xray.com"],
  "expectedIPs": ["geoip:cn"],
  "unexpectedIPs": ["geoip:cloudflare"],
  "skipFallback": false,
  "clientIP": "1.2.3.4",
  "queryStrategy": "UseIPv4",
  "timeoutMs": 4000,
  "disableCache": false,
  "finalQuery": false
}
```

More specific configurations such as `address`, `port`, `domains`, and `expectedIPs` are detailed in the configuration to specify behaviors and DNS query strategies.

> **TIP**: For detailed configuration and the interpretation of local mode and DNS server domain names, ensure addresses are explicitly mapped in DNS options to prevent potential loops, especially within transparent proxies.
