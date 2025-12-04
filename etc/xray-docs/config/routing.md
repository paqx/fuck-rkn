# Routing

The routing module can direct inbound data through different outbound connections based on different rules to achieve on-demand proxy purposes.

A common use is to split domestic and international traffic. Xray can determine traffic from different regions through internal mechanisms and then send them to different outbound proxies.

More detailed analysis on routing features: [Routing Feature Analysis](/document/level-1/routing-lv1-part1.html).

## RoutingObject

`RoutingObject` corresponds to the `routing` item in the configuration file.

```json
{
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [],
    "balancers": []
  }
}
```

`domainStrategy`: "AsIs" | "IPIfNonMatch" | "IPOnDemand"

Domain resolution strategy, using different strategies based on different settings.

- `"AsIs"`: No additional operations, use the domain name in the target address or the sniffed domain name. Default value.
- `"IPIfNonMatch"`: After a full round of matches, if no rules are hit, resolve the domain name to IP for a second match.
- `"IPOnDemand"`: Before matching starts, resolve the domain name to IP for matching.

The actual resolution behavior will be delayed until IP rules are first encountered to reduce latency. The result will include both IPv4 and IPv6 (you can further restrict in the built-in DNS's `queryStrategy`). When multiple IPs are resolved, each rule will try all IPs in turn and then match the next route (if the rule is not hit).

When sniffing + routeOnly is enabled, allowing the routing system to see both IP and domain, if the above resolution occurs, the routing system can only see IPs resolved from the domain and cannot see the original target IP, unless resolution fails.

When there are two domains (target domain + sniff result), the sniff result always has a higher priority for resolution or domain matching.

Regardless of resolution, the routing system does not affect the actual target address; the request's target remains the original target.

`rules`: [RuleObject]

This corresponds to an array where each item is a rule.

For each connection, the routing will be judged sequentially based on these rules from top to bottom. When the first effective rule is encountered, it redirects the connection to its specified `outboundTag` or `balancerTag`.

:::tip
If no rules are matched, traffic is sent via the first outbound by default.
:::

`balancers`: [BalancerObject]

This is an array, where each item is a load balancer configuration.

When a rule points to a load balancer, Xray selects an outbound via the load balancer and forwards the traffic through it.

### RuleObject

```json
{
  "domain": ["baidu.com", "qq.com", "geosite:cn"],
  "ip": ["0.0.0.0/8", "10.0.0.0/8", "fc00::/7", "fe80::/10", "geoip:cn"],
  "port": "53,443,1000-2000",
  "sourcePort": "53,443,1000-2000",
  "localPort": "53,443,1000-2000",
  "network": "tcp",
  "sourceIP": ["10.0.0.1"],
  "localIP": ["192.168.0.25"],
  "user": ["love@xray.com"],
  "vlessRoute": "53,443,1000-2000",
  "inboundTag": ["tag-vmess"],
  "protocol": ["http", "tls", "quic", "bittorrent"],
  "attrs": { ":method": "GET" },
  "outboundTag": "direct",
  "balancerTag": "balancer",
  "ruleTag": "rule name"
}
```

:::danger
When multiple attributes are specified at the same time, these attributes need to be satisfied simultaneously for the rule to take effect.
:::

`domain`: [string]

This is an array where each item is a domain match. It can take the following forms:

- Pure string: When this string matches any part of the target domain, the rule takes effect. For example, "sina.com" can match "sina.com", "sina.com.cn", and "www.sina.com", but not "sina.cn".
- Regular expression: Starting with `"regexp:"`, followed by a regular expression. When this regex matches the target domain, the rule is effective. For example, `"regexp:\\\\.goo.\\*\\\\.com\$"` matches "www.google.com" or "fonts.googleapis.com", but not "google.com". (Note: In JSON, backslashes often used in regex must be escaped, so backslashes in regex should be represented as `\\`.)
- Subdomain (recommended): Starting with `"domain:"`, the remainder is a domain. When this domain is the target domain or its subdomain, the rule is effective. For example, "domain:xray.com" matches "www.xray.com", "xray.com", but not "wxray.com".
- Full match: Starting with `"full:"`, the remainder is a domain. When this domain fully matches the target domain, the rule is effective. For example, "full:xray.com" matches "xray.com" but not "www.xray.com".
- Predefined domain list: Starting with `"geosite:"` followed by a name, such as `geosite:google` or `geosite:cn`. Refer to [Predefined Domain List](#预定义域名列表) for names and domain lists.
- Load domains from file: In the form `"ext:file:tag"`, starting with `ext:` (lowercase), followed by the filename and tag. The file is stored in the [Resource Path](/config/features/env.html#%E8%B5%84%E6%BA%90%E6%96%87%E4%BB%B6%E8%B7%AF%E5%BE%84) and has the same format as `geosite.dat`, where the tag must exist in the file.

:::tip
`"ext:geoip.dat:cn"` is equivalent to `"geoip:cn"`
:::

`ip`: [string]

This is an array where each item represents an IP range. When an item matches the target IP, the rule takes effect. It can take the following forms:

- IP: Such as `"127.0.0.1"`.
- [CIDR](https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing): Such as `"10.0.0.0/8"`, and you can use `"0.0.0.0/0"` or `"::/0"` to specify all IPv4 or IPv6.
- Predefined IP list: This list is preset in every Xray installation package as `geoip.dat`. Use in the form `"geoip:cn"`, starting with `geoip:` (lowercase) followed by a double-character country code. Supports almost all countries capable of accessing the internet.
  - Special value: `"geoip:private"`, includes all private addresses such as `127.0.0.1`.
  - Negative selection (!): `"geoip:!cn"` indicates non-geoip:cn results.
- Load IP from file: In the form `"ext:file:tag"`, starting with `ext:` (lowercase), followed by the filename and tag. The file is stored in the [Resource Path](/config/features/env.html#%E8%B5%84%E6%BA%90%E6%96%87%E4%BB%B6%E8%B7%AF%E5%BE%84) and has the same format as `geoip.dat`, where the tag must exist in the file.

`port`: number | string

Target port range, in three forms:

- `"a-b"`: a and b are positive integers less than 65536. This range is closed, and when the target port falls within it, the rule is effective.
- `a`: a is a positive integer less than 65536. When the target port is a, the rule is effective.
- A mix of the above two forms, separated by commas: `"53,443,1000-2000"`.

`sourcePort`: number | string

Source port, in three forms:

- `"a-b"`: a and b are positive integers less than 65536. This range is closed, and when the target port falls within it, the rule is effective.
- `a`: a is a positive integer less than 65536. When the target port is a, the rule is effective.
- A mix of the above two forms, separated by commas: `"53,443,1000-2000"`.

`localPort`: number | string

Local inbound port; the format is the same as `port`/`sourcePort`. It may be useful when monitoring a port range inbound.

`network`: "tcp" | "udp" | "tcp,udp"

Possible values are "tcp", "udp", or "tcp,udp". When the connection method is the specified one, the rule takes effect.

Since the core clearly supports only two layer-4 protocols (tcp and udp), a route that includes only the `"network": "tcp,udp"` condition can be used to catch all and match any traffic. An example of usage is to place it at the end of all routing rules to specify the default outbound used when no other rule is matched (otherwise, the core defaults to the first).

Of course, other clearly all-encompassing methods such as specifying port 1-65535 or IP `0.0.0.0/0` + `::/0` have similar effects.

`sourceIP`: [string]

This is an array where each item represents an IP range in the forms of IP, CIDR, GeoIP, and loading IP from a file. When an item matches the source IP, the rule takes effect.

Alias: `source`

`localIP`: [string]

The same format as other IPs, used to specify the local inbound IP (when using 0.0.0.0 to listen on all IPs, different actual incoming IPs will produce different localIP).

Not effective for UDP (due to the packet-oriented nature of UDP, it cannot track), always seeing the listen IP.

`user`: [string]

This is an array where each item is an email address. When an item matches the source user, the rule takes effect.

Similar to domain, it also supports regex matching starting with `"regexp:"`. (Similarly, replace `\` with `\\` as explained in the domain section.)

`vlessRoute`: number | string

VLESS inbound allows the configured UUID's seventh and eighth bytes to be modified to any bytes by the client. The server-side routing will take this as vlessRoute data, allowing users to customize part of the server-side routing as needed without changing any external fields.

```text
--------------↓↓↓↓------------------
xxxxxxxx-xxxx-0000-xxxx-xxxxxxxxxxxx
```

In the configuration, it uses big-endian encoded data as uint16 (if not understood, treat these four digits as a hexadecimal number and convert to decimal), e.g., `0001→1` `000e→14` `38b2→14514`. The reason for this format is the same as that for the `port`, allowing free specification of many segments for routing.

`inboundTag`: [string]

This is an array where each item is an identifier. When an item matches the inbound protocol's identifier, the rule takes effect.

`protocol`: [ "http" | "tls" | "quic" | "bittorrent" ]

An array where each item represents a protocol. When a protocol matches the current connection protocol type, the rule takes effect.

`http` only supports 1.0 and 1.1, h2 is not supported yet (plaintext h2 traffic is also very rare).

`tls` TLS 1.0 ~ 1.3

`quic` Due to the complexity of this protocol, sniffing may fail sometimes.

`bittorrent` Only basic sniffing is supported; many encryptions and obfuscations may not work.

:::tip
The `sniffing` option in the inbound proxy must be enabled to sniff the protocol type used by the connection.
:::

`attrs`: object

This is a JSON object where both the keys and values are strings, used to detect attribute values of HTTP traffic (for obvious reasons, only supports 1.0 and 1.1). When HTTP headers contain all specified keys and the values contain the specified substring, this rule is hit. Keys are case-insensitive. Values support using regex.

It also supports pseudo-headers like h2 `:method` and `:path` for matching methods and paths (although these headers do not exist in HTTP/1.1).

For non-CONNECT HTTP inbound methods, `attrs` can be obtained directly; for other inbounds, sniffing must be enabled to obtain these values for matching.

Examples:

- Detect HTTP GET: `{"method": "GET"}`
- Detect HTTP Path: `{"path": "/test"}`
- Detect Content Type: `{"accept": "text/html"}`

`outboundTag`: string

Corresponds to an outbound's identifier.

`balancerTag`: string

Corresponds to a Balancer's identifier.

:::tip
`balancerTag` and `outboundTag` must choose one. When both are specified, `outboundTag` takes effect.
:::

`ruleTag`: string

Optional, no actual effect, only used to identify the name of this rule.

If set, relevant information will be output at the Info level when this rule is hit, used to debug which rule was hit specifically.

### BalancerObject

Load balancer configuration. When a load balancer takes effect, it selects the most suitable outbound from the specified outbounds according to the configuration for traffic forwarding.

```json
{
  "tag": "balancer",
  "selector": [],
  "fallbackTag": "outbound",
  "strategy": {}
}
```

`tag`: string

The identifier of this load balancer, used to match the `balancerTag` in `RuleObject`.

`selector`: [ string ]

A string array, where each string will be used for prefix matching with outbound identifiers. Among the following outbound identifiers: `["a", "ab", "c", "ba"]`, `"selector": ["a"]` will match to `["a", "ab"]`.

Typically matches multiple outbounds so they can share the load.

`fallbackTag`: string

If all observed outbounds cannot connect based on connection results, use the outbound specified by this configuration item.

Note: Add [obsObservatory](/config/observatory.html#observatoryobject) or [burstObservatory](/config/observatory.html#burstobservatoryobject) configuration items.

`strategy`: StrategyObject

#### StrategyObject

```json
{
  "type": "roundRobin",
  "settings": {}
}
```

`type`: "random" | "roundRobin" | "leastPing" | "leastLoad"

- `random` Default value. Randomly selects a matching outbound proxy.
- `roundRobin` Selects matching outbound proxy in sequence.
- `leastPing` Selects the outbound proxy with the smallest latency according to connection observation results. Requires adding [obsObservatory](/config/observatory.html#observatoryobject) or [burstObservatory](/config/observatory.html#burstobservatoryobject) configuration items.
- `leastLoad` Selects the most stable outbound proxy according to connection observation results. Requires adding [obsObservatory](/config/observatory.html#observatoryobject) or [burstObservatory](/config/observatory.html#burstobservatoryobject) configuration items.

:::tip
No matter the mode, if all the `selector` corresponding nodes are simultaneously configured with `observatory` or `burstObservatory`, you can filter out healthy nodes. If there are no healthy nodes available, `fallbackTag` will be attempted.
:::

`settings`: StrategySettingsObject

#### StrategySettingsObject

This is an optional configuration item. The configuration format varies for different load balancing strategies. Currently, only the `leastLoad` load balancing strategy can add this configuration item.

```json
{
  "expected": 2,
  "maxRTT": "1s",
  "tolerance": 0.01,
  "baselines": ["1s"],
  "costs": [
    {
      "regexp": false,
      "match": "tag",
      "value": 0.5
    }
  ]
}
```

`expected`: number

The number of optimal nodes selected by the load balancer; traffic will be distributed randomly among these nodes.

`maxRTT`: string

The maximum acceptable RTT duration for speed testing.

`tolerance`: float number

The maximum acceptable speed test failure ratio, such as 0.01 indicating 1% acceptable speed test failure. (Apparently not implemented.)

`baselines`: [ string ]

The maximum acceptable standard deviation duration for speed test RTT.

`costs`: [ CostObject ]

Optional configuration item, an array that can assign weights to all outbounds.

`regexp`: true | false

Whether to use a regex expression to select outbound `Tag`.

`match`: string

Matches outbound `Tag`.

`value`: float number

The weight value; the larger the value, the less likely the corresponding node is selected.

### Load Balancer Configuration Example

```json
"routing": {
    "rules": [
        {
            "inboundTag": [
                "in"
            ],
            "balancerTag": "round"
        }
    ],
    "balancers": [
        {
            "selector": [
                "out"
            ],
            "strategy": {
                "type": "roundRobin"
            },
            "tag": "round"
        }
    ]
}

"inbounds": [
    {
        // Inbound configuration
        "tag": "in"
    }
]

"outbounds": [
    {
        // Outbound configuration
        "tag": "out1"
    },
    {
        // Outbound configuration
        "tag": "out2"
    }
]
```

### Predefined Domain List

This list is preset in every Xray installation package as `geosite.dat`. This file contains some common domain names, using the method: `geosite:filename`, such as `geosite:google` for domain routing or DNS filtering that matches the domain names included in the `google` file.

Common domains include:

- `category-ads`: Includes common ad domains.
- `category-ads-all`: Includes common ad domains and advertiser domains.
- `cn`: Equivalent to combining `geolocation-cn` and `tld-cn`.
- `apple`: Contains most domains under Apple.
- `google`: Contains most domains under Google.
- `microsoft`: Contains most domains under Microsoft.
- `facebook`: Contains most domains under Facebook.
- `twitter`: Contains most domains under Twitter.
- `telegram`: Contains most domains under Telegram.
- `geolocation-cn`: Includes common Mainland China site domains.
- `geolocation-!cn`: Includes common non-Mainland China site domains.
- `tld-cn`: Includes top-level domains managed by CNNIC for Mainland China, such as domains ending with `.cn`, `.中国`.
- `tld-!cn
