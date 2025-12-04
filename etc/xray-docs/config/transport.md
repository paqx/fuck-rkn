# Transmission Methods (uTLS, REALITY)

Transmission methods (transport) are the ways current Xray nodes interface with other nodes.

Transmission methods specify stable data transmission methods. Typically, both ends of a network connection need a symmetric transmission method. For example, if one end uses WebSocket, the other must use WebSocket as well; otherwise, a connection cannot be established.

## StreamSettingsObject

`StreamSettingsObject` corresponds to the `streamSettings` item in inbound or outbound. Each inbound or outbound can configure different transmission settings, allowing the setup of `streamSettings` for transportation configurations.

```json
{
  "network": "raw",
  "security": "none",
  "tlsSettings": {},
  "realitySettings": {},
  "rawSettings": {},
  "xhttpSettings": {},
  "kcpSettings": {},
  "grpcSettings": {},
  "wsSettings": {},
  "httpupgradeSettings": {},
  "sockopt": {
    "mark": 0,
    "tcpMaxSeg": 1440,
    "tcpFastOpen": false,
    "tproxy": "off",
    "domainStrategy": "AsIs",
    "happyEyeballs": {},
    "dialerProxy": "",
    "acceptProxyProtocol": false,
    "tcpKeepAliveInterval": 0,
    "tcpKeepAliveIdle": 300,
    "tcpUserTimeout": 10000,
    "tcpCongestion": "bbr",
    "interface": "wg0",
    "v6only": false,
    "tcpWindowClamp": 600,
    "tcpMptcp": false
  }
}
```

> `network`: "raw" | "xhttp" | "kcp" | "grpc" | "ws" | "httpupgrade"

The type of transmission method used for the data stream connection, default is `"raw"`.

> **Tip**  
> From version v24.9.30 onwards, TCP transmission method has been renamed to RAW for closer alignment with real-world behavior. For compatibility, `"network": "raw"` and `"network": "tcp"`, `rawSettings` and `tcpSettings` are aliases.

> `security`: "none" | "tls" | "reality"

Whether to enable transport layer encryption, options are:
- `"none"`: no encryption (default)
- `"tls"`: use [TLS](https://en.wikipedia.org/wiki/Transport_Layer_Security).
- `"reality"`: use REALITY.

> `tlsSettings`: [TLSObject](#tlsobject)

TLS configuration. TLS is provided by Golang, usually resulting in the use of TLS 1.3, DTLS not supported.

> `realitySettings`: [RealityObject](#realityobject)

Reality configuration. Reality is Xray’s original tech. It offers higher security than TLS, with similar configuration methods.

> **Tip**  
> Reality is currently the safest transmission encryption scheme, offering normal internet traffic consistency and significant performance improvements when used with the appropriate XTLS Vision flow control mode.

> `rawSettings`: [RawObject](https://example.com/config/transports/raw.html)

RAW configuration for the current connection, only applicable when RAW is used.

> `xhttpSettings`: [XHTTP: Beyond REALITY](https://github.com/XTLS/Xray-core/discussions/4113)

XHTTP configuration for the current connection, only applicable when XHTTP is used.

> `kcpSettings`: [KcpObject](https://example.com/config/transports/mkcp.html)

mKCP configuration for the current connection, only applicable when mKCP is used.

> `grpcSettings`: [GRPCObject](https://example.com/config/transports/grpc.html)

gRPC configuration for the current connection, only applicable when gRPC is used.

> `wsSettings`: [WebSocketObject](https://example.com/config/transports/websocket.html)

WebSocket configuration for the current connection, only applicable when WebSocket is used.

> `httpupgradeSettings`: [HttpUpgradeObject](https://example.com/config/transports/httpupgrade.html)

HTTPUpgrade configuration for the current connection, only applicable when HTTPUpgrade is used.

> `sockopt`: [SockoptObject](#sockoptobject)

Detailed configuration related to transparent proxying.

### TLSObject

```json
{
  "serverName": "xray.com",
  "verifyPeerCertInNames": [],
  "rejectUnknownSni": false,
  "allowInsecure": false,
  "alpn": ["h2", "http/1.1"],
  "minVersion": "1.2",
  "maxVersion": "1.3",
  "cipherSuites": "list of cipher suite names separated by :",
  "certificates": [],
  "disableSystemRoot": false,
  "enableSessionResumption": false,
  "fingerprint": "",
  "pinnedPeerCertificateChainSha256": [""],
  "curvePreferences": [""],
  "masterKeyLog": "",
  "echServerKeys": "",
  "echConfigList": "",
  "echForceQuery": "",
  "echSockopt": {}
}
```

> `serverName`: string

Specifies the domain name of the server-side certificate, useful when the connection is established by IP. When left empty, automatically uses the value from the address (if a domain), which is also used to verify the server certificate's validity.

> `verifyPeerCertInNames`: [ string ]

For client use, specifies a list of SNIs for certificate verification. Overrides the `serverName` for verification purposes, used for domain fronting and other special needs.

> `rejectUnknownSni`: bool

When set to `true`, the server rejects the TLS handshake if the received SNI does not match the certificate domain.

> `alpn`: [ string ]

An array of strings specifying ALPN numbers in the TLS handshake. Default is `["h2", "http/1.1"]`.

> `minVersion`: string

Minimum acceptable TLS version.

> `maxVersion`: string

Maximum acceptable TLS version.

> `cipherSuites`: string

Configures supported cipher suites list, separated by `:`.

> **Warning**  
> These settings are optional and typically do not affect security when not configured. Issues caused by incorrect configuration are your own responsibility.

> `allowInsecure`: true | false

Allows insecure connections (client only). Default is `false`. When `true`, Xray does not check the validity of the TLS certificate provided by the remote host.

> **Warning**  
> For security reasons, this option should not be set to true in actual scenarios to avoid man-in-the-middle attacks.

> `disableSystemRoot`: true | false

Disables the use of system CA certificates. Default is `false`.

> `enableSessionResumption`: true | false

Enables session resumption, disabled by default. It must be enabled on both server and client for session resumption to be negotiated.

> `fingerprint`: string

Used to configure the specified `TLS Client Hello` fingerprint. Default is `chrome`.

- Common browser TLS fingerprints include:
  - `"chrome"`, `"firefox"`, `"safari"`, `"ios"`, `"android"`, `"edge"`, `"360"`, `"qq"`
- Automatically generating a fingerprint at the start of Xray:
  - `"random"`, `"randomized"`
- Using native uTLS fingerprint variable names, e.g., `"HelloRandomizedNoALPN"`, `"HelloChrome_106_Shuffle"`. Complete list can be found in the [uTLS library](https://github.com/refraction-networking/utls/blob/master/u_common.go#L434).

> `pinnedPeerCertificateChainSha256`: [string]

Specifies the SHA256 hash of the remote server's certificate chain, using standard encoding format.

> `certificates`: [CertificateObject](#certificateobject)

A list of certificates, each representing a certificate (full chain recommended).

### RealityObject

```json
{
  "show": false,
  "target": "example.com:443",
  "xver": 0,
  "serverNames": ["example.com", "www.example.com"],
  "privateKey": "",
  "minClientVer": "",
  "maxClientVer": "",
  "maxTimeDiff": 0,
  "shortIds": ["", "0123456789abcdef"],
  "mldsa65Seed": "",
  "limitFallbackUpload": {
    "afterBytes": 0,
    "bytesPerSec": 0,
    "burstBytesPerSec": 0
  },
  "limitFallbackDownload": {
    "afterBytes": 0,
    "bytesPerSec": 0,
    "burstBytesPerSec": 0
  },
  "fingerprint": "chrome",
  "serverName": "",
  "password": "",
  "shortId": "",
  "mldsa65Verify": "",
  "spiderX": ""
}
```

> **Tip**  
> For more information, refer to the [REALITY project](https://github.com/XTLS/REALITY).

> `show`: true | false

Outputs debugging information when `true`.

#### Inbound (Server-Side) Configuration

> `target`: string

Required, formatted the same as VLESS `fallbacks`'s dest.

> **Note**  
> To prevent unwanted scenarios, consider filtering unqualified SNIs before forwarding, or configure `limitFallbackUpload` and `limitFallbackDownload` to limit rate.

> `xver`: number

Optional, same format as VLESS `fallbacks`'s xver.

> `serverNames`: [string]

Required, list of client-usable `serverName`s.

> `privateKey`: string

Required, generated with `./xray x25519`.

> `minClientVer`: string

Optional, minimum client Xray version in `x.y.z` format.

> `maxClientVer`: string

Optional, maximum client Xray version in `x.y.z` format.

> `maxTimeDiff`: number

Optional, maximum allowed time difference in milliseconds.

> `shortIds`: [string]

Required, a list of client-usable `shortId`s, allowing differentiation between clients.

#### Outbound (Client-Side) Configuration

> `serverName`: string

One of the server's `serverNames`.

> `fingerprint`: string

Required, same as [TLSObject](#tlsobject). Note: `unsafe` is not supported to disable utls here as the REALITY protocol uses this library to manipulate underlying TLS parameters.

> `shortId`: string

One of the server's `shortIds`.

> `password`: string

Required, the server's private key corresponding public key.

### SockoptObject

```json
{
  "mark": 0,
  "tcpMaxSeg": 1440,
  "tcpFastOpen": false,
  "tproxy": "off",
  "domainStrategy": "AsIs",
  "happyEyeballs": {},
  "dialerProxy": "",
  "acceptProxyProtocol": false,
  "tcpKeepAliveInterval": 0,
  "tcpKeepAliveIdle": 300,
  "tcpUserTimeout": 10000,
  "tcpCongestion": "bbr",
  "interface": "wg0",
  "V6Only": false,
  "tcpWindowClamp": 600,
  "tcpMptcp": false,
  "addressPortStrategy": "",
  "customSockopt": []
}
```

> `mark`: number

An integer marking SO_MARK on outbound connections when non-zero.

> `tcpMaxSeg`: number

Sets the maximum segment size for TCP packets.

> `tcpFastOpen`: true | false | number

Enables [TCP Fast Open](https://en.wikipedia.org/wiki/TCP_Fast_Open).

> `tproxy`: "redirect" | "tproxy" | "off"

Enables transparent proxying (Linux only).

> `domainStrategy`: "AsIs" | "UseIP" | "UseIPv6v4" | "UseIPv6" | "UseIPv4v6" | "UseIPv4" | "ForceIP" | "ForceIPv6v4" | "ForceIPv6" | "ForceIPv4v6" | "ForceIPv4"

Defines outbound connection behavior based on the target, with `"AsIs"` as default.

> `dialerProxy`: ""

Specifies an outbound proxy identifier.

> `acceptProxyProtocol`: true | false

For inbound use, indicates whether to accept the PROXY protocol.

> `tcpKeepAliveIdle`: number

TCP idle time threshold in seconds before sending Keep-Alive probes.

> `tcpKeepAliveInterval`: number

Interval between Keep-Alive packets in seconds once the TCP connection reaches the Keep-Alive state.

> `tcpUserTimeout`: number

Measured in milliseconds.

> `tcpCongestion`: ""

TCP congestion control algorithm, Linux only.

> `interface`: ""

Specifies the network interface to bind to.

> `V6Only`: true | false

When `true`, the `::` address only accepts IPv6 connections, supported on Linux only.

> `tcpWindowClamp`: number

Sets the advertised window size.

> `tcpMptcp`: true | false

Enables Multipath TCP, client-side only, supported on Linux with Kernel 5.6+.

> `customSockopt`: []

An array for advanced users to specify any required socket options.

### CertificateObject

```json
{
  "ocspStapling": 0,
  "oneTimeLoading": false,
  "usage": "encipherment",
  "buildChain": false,
  "certificateFile": "/path/to/certificate.crt",
  "keyFile": "/path/to/key.key",
  "certificate": [
    "--BEGIN CERTIFICATE--",
    "MIICwDCCAaigAwIBAgIRAO16JMdESAuHidFYJAR/7kAwDQYJKoZIhvcNAQELBQAw",
    "ADAeFw0xODA0MTAxMzU1MTdaFw0xODA0MTAxNTU1MTdaMAAwggEiMA0GCSqGSIb3",
    "DQEBAQUAA4IBDwAwggEKAoIBAQCs2PX0fFSCjOemmdm9UbOvcLctF94Ox4BpSfJ+",
    "3lJHwZbvnOFuo56WhQJWrclKoImp/c9veL1J4Bbtam3sW3APkZVEK9UxRQ57HQuw",
    "OzhV0FD20/0YELou85TwnkTw5l9GVCXT02NG+pGlYsFrxesUHpojdl8tIcn113M5",
    "pypgDPVmPeeORRf7nseMC6GhvXYM4txJPyenohwegl8DZ6OE5FkSVR5wFQtAhbON",
    "OAkIVVmw002K2J6pitPuJGOka9PxcCVWhko/W+JCGapcC7O74palwBUuXE1iH+Jp",
    "noPjGp4qE2ognW3WH/sgQ+rvo20eXb9Um1steaYY8xlxgBsXAgMBAAGjNTAzMA4G",
    "A1UdDwEB/wQEAwIFoDATBgNVHSUEDDAKBggrBgEFBQcDATAMBgNVHRMBAf8EAjAA",
    "MA0GCSqGSIb3DQEBCwUAA4IBAQBUd9sGKYemzwPnxtw/vzkV8Q32NILEMlPVqeJU",
    "7UxVgIODBV6A1b3tOUoktuhmgSSaQxjhYbFAVTD+LUglMUCxNbj56luBRlLLQWo+",
    "9BUhC/ow393tLmqKcB59qNcwbZER6XT5POYwcaKM75QVqhCJVHJNb1zSEE7Co7iO",
    "6wIan3lFyjBfYlBEz5vyRWQNIwKfdh5cK1yAu13xGENwmtlSTHiwbjBLXfk+0A/8",
    "r/2s+sCYUkGZHhj8xY7bJ1zg0FRalP5LrqY+r6BckT1QPDIQKYy615j1LpOtwZe/",
    "d4q7MD/dkzRDsch7t2cIjM/PYeMuzh87admSyL6hdtK0Nm/Q",
    "--END CERTIFICATE--"
  ],
  "key": [
    "--BEGIN RSA PRIVATE KEY--",
    "MIIEowIBAAKCAQEArNj19HxUgoznppnZvVGzr3C3LRfeDseAaUnyft5SR8GW75zh",
    "bqOeloUCVq3JSqCJqf3Pb3i9SeAW7Wpt7FtwD5GVRCvVMUUOex0LsDs4VdBQ9tP9",
    "GBC6LvOU8J5E8OZfRlQl09NjRvqRpWLBa8XrFB6aI3ZfLSHJ9ddzOacqYAz1Zj3n",
    "jkUX+57HjAuhob12DOLcST8np6IcHoJfA2ejhORZElUecBULQIWzjTgJCFVZsNNN",
    "itieqYrT7iRjpGvT8XAlVoZKP1viQhmqXAuzu+KWpcAVLlxNYh/iaZ6D4xqeKhNq",
    "IJ1t1h/7IEPq76NtHl2/VJtbLXmmGPMZcYAbFwIDAQABAoIBAFCgG4phfGIxK9Uw",
    "qrp+o9xQLYGhQnmOYb27OpwnRCYojSlT+mvLcqwvevnHsr9WxyA+PkZ3AYS2PLue",
    "C4xW0pzQgdn8wENtPOX8lHkuBocw1rNsCwDwvIguIuliSjI8o3CAy+xVDFgNhWap",
    "/CMzfQYziB7GlnrM6hH838iiy0dlv4I/HKk+3/YlSYQEvnFokTf7HxbDDmznkJTM",
    "aPKZ5qbnV+4AcQfcLYJ8QE0ViJ8dVZ7RLwIf7+SG0b0bqloti4+oQXqGtiESUwEW",
    "/Wzi7oyCbFJoPsFWp1P5+wD7jAGpAd9lPIwPahdr1wl6VwIx9W0XYjoZn71AEaw4",
    "bK4xUXECgYEA3g2o9Wq