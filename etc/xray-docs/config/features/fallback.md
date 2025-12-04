# Fallback

> **Fallback is one of Xray's most powerful features, effectively preventing active probing and freely configuring shared services on common ports.**

Fallback provides Xray with high resistance to active probing and features a unique first-packet fallback mechanism.

Fallback can also distribute different types of traffic based on path, enabling multiple service sharing on a single port.

Currently, you can utilize fallbacks by configuring them when using the VLESS or Trojan protocols to create diverse combinations.

## Fallbacks Configuration

```json
"fallbacks": [
  {
    "dest": 80
  }
]
```

> `fallbacks`: [ [FallbackObject](#fallbackobject) ]

An array containing a series of powerful fallback distribution configurations.

### FallbackObject

```json
{
  "name": "",
  "alpn": "",
  "path": "",
  "dest": 80,
  "xver": 0
}
```

**`fallbacks` is an array, and here is the configuration description for one of its elements.**

- The `fallbacks` item is optional and can only be used with the TCP+TLS transport combination.
- When this item has sub-elements, [Inbound TLS](https://example.com/config/transport.html#tlsobject) should set `"alpn":["http/1.1"]`.**
  
Generally, you need to first set a default fallback where `alpn` and `path` are omitted or empty, then configure other distributions as needed.

VLESS will forward traffic with TLS decrypted first packet length < 18 or invalid protocol version and failed authentication to the specified address in `dest`.

Other transport combinations must delete the `fallbacks` item or all sub-elements, and Fallback will not be enabled in this case. VLESS will wait for the required length, and will disconnect directly if the protocol version is invalid or authentication fails.

> `name`: string

Attempts to match TLS SNI (Server Name Indication), empty for any, default is ""

> `alpn`: string

Attempts to match the TLS ALPN negotiation result, empty for any, default is ""

When needed, VLESS will attempt to read the TLS ALPN negotiation result. If successful, it outputs `realAlpn =` to the log. Usage: Resolves the issue of Nginx’s h2c service not being compatible with http/1.1 simultaneously. Nginx requires two lines of listen for 1.1 and h2c. Note: When `fallbacks` alpn contains `"h2"`, [Inbound TLS](https://example.com/config/transport.html#tlsobject) should set `"alpn":["h2","http/1.1"]` to support h2 access.

> **Tip**

The `alpn` set within Fallback matches the actual negotiated ALPN, while the Inbound TLS set `alpn` is the optional ALPN list during the handshake. They have different meanings.

> `path`: string

Attempts to match the first packet HTTP PATH, empty for any, default is empty. Non-empty must start with `/` and does not support h2c.

Smart: When needed, VLESS will briefly check the PATH (not exceeding 55 bytes; the fastest algorithm without fully parsing HTTP). If successful, it outputs `realPath =` INFO log. Usage: Distributes other inbound WebSocket traffic or HTTP masquerade traffic, purely forwarding traffic with no extra processing, theoretically more performant than Nginx.

Note: **Fallbacks must be TCP+TLS for the inbound itself**, which is used to distribute to other WS inbounds. The distributed inbound does not require TLS configuration.

> `dest`: string | number

Determines the destination of the TCP traffic after TLS decryption. Currently supports two address types (this item is required, otherwise it cannot start):

1. TCP, formatted as `"addr:port"`, where addr supports IPv4, domain, IPv6. If a domain is filled, a direct TCP connection will be initiated (without using built-in DNS).
2. Unix domain socket, formatted as an absolute path like `"/dev/shm/domain.socket"`, with `@` at the start representing [abstract](https://www.man7.org/linux/man-pages/man7/unix.7.html), and `@@` representing padded abstract.

If only the port is filled, it can be a number or string, like `80`, `"80"`, usually pointing to a plaintext HTTP service (addr will be supplemented as `"localhost"`).

Note: After v25.7.26, `dest` containing only the port points to localhost. Before this, it always pointed to 127.0.0.1. This change means the actual target might be ::1, and some copied templates on the web might listen on ::1 while only allowing 127 or applying proxy protocol, possibly causing different behavior.

> `xver`: number

Sends [PROXY protocol](https://www.haproxy.org/download/2.2/doc/proxy-protocol.txt), used to transmit the real source IP and port of the request. Fill version 1 or 2, default is 0, meaning no sending. If needed, it is recommended to fill 1.

Currently, filling 1 or 2, the functionality is entirely the same, just different structures, with the former being printable and the latter binary. Xray’s TCP and WS inbound both support receiving PROXY protocol.

> **Warning**

If you are [configuring Nginx to receive PROXY protocol](https://docs.nginx.com/nginx/admin-guide/load-balancer/using-proxy-protocol/#configuring-nginx-to-accept-the-proxy-protocol), apart from setting proxy_protocol, set_real_ip_from must also be configured, otherwise issues might arise.

### Additional Notes

- The most accurate sub-element will be matched first, regardless of the order of sub-elements. If several sub-elements are configured with the same `alpn` and `path`, the last one will take precedence.
- Fallback and routing is TCP-layer forwarding after decryption, not HTTP-layer, only checking the first packet PATH when necessary.
- For more tips and insights on using Fallbacks, see:
  - [Fallbacks Function Analysis](../../document/level-1/fallbacks-lv1)
