# Reverse Proxy

A reverse proxy forwards server-side traffic to the client, i.e., reverse traffic forwarding.

::: tip
This reverse proxy is a general purpose one (not limited by protocol type), and its configuration is more complex. Do not confuse it with the VLESS simple configuration reverse (see the relevant sections of the VLESS inbound and outbound documentation).
:::

Its underlying protocol is Mux.cool, but the direction is reversed, with the server initiating requests to the client.

The basic working principle of a reverse proxy is as follows:

- Suppose there is a web server on Host A, which does not have a public IP and cannot be accessed directly on the internet. There is another Host B, which can be accessed publicly. Now, we need to use B as the entry point to forward traffic from B to A.

  - Configure Xray on Host B to receive external requests, thus termed as `portal`.
  - Configure Xray on Host A to bridge the forward from B and the web server, termed as `bridge`.

- **`bridge`**

  - `bridge` actively establishes a connection to `portal` to register a reverse channel. The target address (domain) for this connection can be set independently.
  - After `bridge` receives the public traffic forwarded by `portal`, it will pass it directly to the web server on Host A. Of course, this step requires configuration of the routing module.
  - After receiving a response, `bridge` will return the response directly to `portal`.

- **`portal`**

  - When `portal` receives a request and the domain matches, it means the response data is sent by `bridge`. This connection will be used to establish a reverse channel.
  - When `portal` receives a request and the domain does not match, it means the connection is coming from a public user. This connection data will be forwarded to the bridge.

- `bridge` will dynamically balance the load according to the size of the traffic.

::: tip
The reverse proxy is enabled by default with [Mux](https://link/to/mux), please do not enable Mux again on its used outbound.
:::

::: warning
The reverse proxy feature is still in the testing phase and may have some issues.
:::

## ReverseObject

`ReverseObject` corresponds to the `reverse` entry in the configuration file.

```json
{
  "reverse": {
    "bridges": [
      {
        "tag": "bridge",
        "domain": "reverse-proxy.xray.internal"
      }
    ],
    "portals": [
      {
        "tag": "portal",
        "domain": "reverse-proxy.xray.internal"
      }
    ]
  }
}
```

> `bridges`: [BridgeObject]

An array, each item represents a `bridge`. Each `bridge` configuration is a [BridgeObject](#bridgeobject).

> `portals`: [PortalObject]

An array, each item represents a `portal`. Each `portal` configuration is a [PortalObject](#portalobject).

### BridgeObject

```json
{
  "tag": "bridge",
  "domain": "reverse-proxy.xray.internal"
}
```

> `tag`: string

All connections initiated by `bridge` will carry this tag. It can be identified in the [routing configuration](https://link/to/config/routing) using `inboundTag`.

> `domain`: string

Specifies a domain name; connections that `bridge` establishes to `portal` will be sent with this domain. This domain is only for communication purposes between `bridge` and `portal` and does not need to actually exist.

### PortalObject

```json
{
  "tag": "portal",
  "domain": "reverse-proxy.xray.internal"
}
```

> `tag`: string

The tag of `portal`. Use `outboundTag` in [routing configuration](https://link/to/config/routing) to forward traffic to this `portal`.

> `domain`: string

A domain name. When `portal` receives traffic, if the target domain name of the traffic is this domain, the portal assumes the current connection is a communication connection from `bridge`. Other traffic will be treated as needing to be forwarded. The work of `portal` is to identify these two types of connections and forward them accordingly.

::: tip
An Xray can function as `bridge`, `portal`, or both, depending on the scenario.
:::

## Complete Configuration Example

::: tip
During operation, it is recommended to enable `bridge` first, and then `portal`.
:::

### Bridge Configuration

`bridge` typically requires two outbounds, one for connecting to the `portal` and another for sending actual traffic. This means you need to distinguish between the two types of traffic using routing.

Reverse Proxy Configuration:

```json
"reverse": {
  "bridges": [
    {
      "tag": "bridge",
      "domain": "reverse-proxy.xray.internal"
    }
  ]
}
```

Outbound:

```json
{
  // Forward to web server
  "tag": "out",
  "protocol": "freedom",
  "settings": {
    "redirect": "127.0.0.1:80"
  }
}
```

```json
{
  // Connect to portal
  "protocol": "vmess",
  "settings": {
    "vnext": [
      {
        "address": "IP address of portal",
        "port": 1024,
        "users": [
          {
            "id": "5783a3e7-e373-51cd-8642-c83782b807c5"
          }
        ]
      }
    ]
  },
  "tag": "interconn"
}
```

Routing Configuration:

```json
{
  "rules": [
    {
      // Requests from bridge with the configured domain indicate an attempt to establish a reverse tunnel to the portal,
      // so route to interconn, i.e., connect to portal
      "type": "field",
      "inboundTag": ["bridge"],
      "domain": ["full:reverse-proxy.xray.internal"],
      "outboundTag": "interconn"
    },
    {
      // Traffic from portal will also come from the bridge but without the above domain,
      // so route to out, i.e., forward to the web server
      "type": "field",
      "inboundTag": ["bridge"],
      "outboundTag": "out"
    }
  ]
}
```

### Portal Configuration

`portal` typically requires two inbounds, one for receiving `bridge` connections and another for receiving actual traffic. You also need to distinguish between the two types of traffic using routing.

Reverse Proxy Configuration:

```json
"reverse": {
  "portals": [
    {
      "tag": "portal",
      "domain": "reverse-proxy.xray.internal" // Must be the same as the bridge configuration
    }
  ]
}
```

Inbound:

```json
{
  // Receive requests directly from the public network
  "tag": "external",
  "port": 80,
  "protocol": "dokodemo-door",
  "settings": {
    "address": "127.0.0.1",
    "port": 80,
    "network": "tcp"
  }
}
```

```json
{
  // Receive requests from bridge attempting to establish a reverse tunnel
  "tag": "interconn",
  "port": 1024,
  "protocol": "vmess",
  "settings": {
    "clients": [
      {
        "id": "5783a3e7-e373-51cd-8642-c83782b807c5"
      }
    ]
  }
}
```

Routing Configuration:

```json
{
  "rules": [
    {
      // If inbound is external, it indicates a request from the public network,
      // so route to portal, which will eventually forward to bridge
      "type": "field",
      "inboundTag": ["external"],
      "outboundTag": "portal"
    },
    {
      // If inbound is from interconn, it indicates a request from bridge attempting to establish a reverse tunnel,
      // so route to portal, which will eventually forward to the corresponding public client
      // Note: the incoming request carries the domain configured earlier, allowing the portal to distinguish two types of requests routed to portal
      "type": "field",
      "inboundTag": ["interconn"],
      "outboundTag": "portal"
    }
  ]
}
```
