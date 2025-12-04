# FakeDNS

FakeDNS reduces DNS query latency by fabricating DNS to obtain the target domain, allowing for domain retrieval with transparent proxies.

> **Warning**  
> FakeDNS may pollute local DNS, leading to network inaccessibility after Xray is closed.

## FakeDNSObject

`FakeDNSObject` corresponds to the `fakedns` item in the configuration file.

```json
{
  "ipPool": "198.18.0.0/16",
  "poolSize": 65535
}
```

`FakeDnsObject` can also be configured as an array with multiple FakeIP Pools. For DNS queries, FakeDNS returns a set of FakeIPs from multiple pools.

```json
[
  {
    "ipPool": "198.18.0.0/15",
    "poolSize": 65535
  },
  {
    "ipPool": "fc00::/18",
    "poolSize": 65535
  }
]
```

### Components

- **`ipPool`: CIDR** - Specifies the IP block for FakeDNS allocation.
- **`poolSize`: int** - Maximum number of domain-IP mappings stored by FakeDNS. Exceeding this value triggers an LRU (least recently used) eviction. Default is 65535.

> **Warning**  
> `poolSize` must not exceed the total address count in `ipPool`.

> **Tip**  
> If the configuration file's `dns` item uses `fakedns` but lacks a `FakeDnsObject` configuration, Xray initializes it using the DNS component's `queryStrategy`.

- **`queryStrategy: UseIP`** initializes with:
  
  ```json
  [
    {
      "ipPool": "198.18.0.0/15",
      "poolSize": 32768
    },
    {
      "ipPool": "fc00::/18",
      "poolSize": 32768
    }
  ]
  ```

- **`queryStrategy: UseIPv4`** initializes with:

  ```json
  {
    "ipPool": "198.18.0.0/15",
    "poolSize": 65535
  }
  ```

- **`queryStrategy: UseIPv6`** initializes with:

  ```json
  {
    "ipPool": "fc00::/18",
    "poolSize": 65535
  }
  ```

### How to Use?

FakeDNS functions as a [DNS server](https://example.com/config/dns.html#serverobject) and can interact with various DNS rules. To utilize it, route DNS queries through FakeDNS.

```json
{
  "dns": {
    "servers": [
      "fakedns", // fakedns first
      "8.8.8.8"
    ]
  },
  "outbounds": [
    {
      "protocol": "dns",
      "tag": "dns-out"
    }
  ],
  "routing": {
    "rules": [
      {
        "type": "field",
        "inboundTag": ["dns-in"], // Capture DNS traffic from queries or transparent proxy
        "port": 53,
        "outboundTag": "dns-out"
      }
    ]
  }
}
```

When external DNS requests enter the FakeDNS component, it returns IP addresses from within its `ipPool` as fictitious resolution results and records the domain-IP mapping.

Additionally, on the **client** with inbound traffic to be proxied, enable `Sniffing` and reset the destination address to `fakedns`.

```json
"sniffing": {
  "enabled": true,
  "destOverride": ["fakedns"], // Use "fakedns" or combine with other sniffers
  "metadataOnly": false        // When true, destOverride can only use fakedns
}
```

> **Warning**  
> Failure to correctly restore FakeIP to domain names will prevent server connections.

### Using with Other DNS Types

#### Coexistence with DNS Sharding

For `fakedns` to have high priority in DNS sharding, add the same `domains` as other DNS types.

```json
{
  "servers": [
    {
      "address": "fakedns",
      "domains": [
        // Matches sharding content below
        "geosite:cn",
        "domain:example.com"
      ]
    },
    {
      "address": "1.2.3.4",
      "domains": ["geosite:cn"],
      "expectIPs": ["geoip:cn"]
    },
    {
      "address": "1.1.1.1",
      "domains": ["domain:example.com"]
    },
    "8.8.8.8"
  ]
}
```

#### FakeDNS Blacklist

To exclude specific domains from FakeDNS, add a `domains` configuration in other DNS types to give them higher priority over FakeDNS.

```json
{
  "servers": [
    "fakedns",
    {
      "address": "1.2.3.4",
      "domains": ["domain:do-not-use-fakedns.com"]
    }
  ]
}
```

#### FakeDNS Whitelist

To use FakeDNS only for specific domains, add a `domains` configuration to `fakedns` for those domains, granting it higher priority over other DNS servers.

```json
{
  "servers": [
    "1.2.3.4",
    {
      "address": "fakedns",
      "domains": ["domain:only-this-use-fakedns.com"]
    }
  ]
}
```
