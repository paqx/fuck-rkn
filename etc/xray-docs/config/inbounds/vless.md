# VLESS (XTLS Vision Seed)

VLESS is a stateless lightweight transmission protocol, divided into inbound and outbound parts, serving as a bridge between Xray clients and servers.

Unlike [VMess](https://example.com/config/inbounds/vmess.html), VLESS does not rely on system time, and uses UUID for authentication.

## InboundConfigurationObject

```json
{
  "clients": [
    {
      "id": "5783a3e7-e373-51cd-8642-c83782b807c5",
      "level": 0,
      "email": "love@xray.com",
      "flow": "xtls-rprx-vision",
      "reverse": {}
    }
  ],
  "decryption": "none",
  "fallbacks": [
    {
      "dest": 80
    }
  ]
}
```

`clients`: [ClientObject]

An array representing a group of users recognized by the server. Each item is a [ClientObject](#clientobject).

`decryption`: "none"

[VLESS encryption](https://github.com/XTLS/Xray-core/pull/5067) setting. Must not be empty; to disable, explicitly set to `"none"`.

It is recommended for most users to use `./xray vlessenc` to automatically generate this field to avoid errors. The detailed configuration below is recommended for advanced users only.

The format consists of a series of fields connected by `.`. For example, `mlkem768x25519plus.native.0rtt.100-111-1111.75-0-111.50-0-3333.ptjHQxBQxTJ9MWr2cd5qWIflBSACHOevTauCQwa_71U`. This document refers to separately dotted parts as blocks.

- The first block is the handshake method, currently only `mlkem768x25519plus` is available. Server and client must be consistent.
- The second block is the encryption method, options are `native`/`xorpub`/`random`, corresponding to: raw format packets/raw format + obfuscate public key part/fully random numbers (similar to VMESS/Shadowsocks). Server and client must be consistent.
- The third block is the session ticket validity period. Format as `600s` or `100-500s`. The former randomly selects a time between the specified length and half (e.g. `600s`=`300-600s`), the latter manually specifies a random range.

Further padding is sent by the server after connection establishment to confuse length features, not required to match the client (the same outbound part is padding sent from the client to the server direction), in `padding.delay.padding`+( `.delay.padding`)*n format (multiple paddings can be inserted, requiring a delay block between two padding blocks). Example: a long `padding.delay.padding.delay.padding.delay.padding.delay.padding.delay.padding`.

- `padding` format is `probability-min-max` such as `100-111-1111`, meaning 100% sends padding with a length of 111~1111.
- `delay` format is also `probability-min-max`, such as `75-0-111`, meaning a 75% probability of waiting 0~111 milliseconds.

The first padding block requires 100% probability and a minimum length greater than 0. If no padding exists, the core automatically uses `100-111-1111.75-0-111.50-0-3333` as padding settings.

The last block is identified by the core as a parameter for authenticating clients, generated using `./xray x25519` (use PrivateKey section) or `./xray mlkem768` (use Seed section), and must correspond to the client. `mlkem768` is a post-quantum algorithm, preventing future clients' parameters from being cracked by quantum computers to impersonate the server. This parameter is for validation only, and the handshake process is always post-quantum secure; existing encrypted data cannot be cracked by future quantum computers.

`fallbacks`: [FallbackObject]

An array containing a series of powerful fallback split routing configurations (optional). For specific configuration of fallbacks, please click [FallbackObject](https://example.com/config/features/fallback.html#fallbacks-configuration).

### ClientObject

```json
{
  "id": "5783a3e7-e373-51cd-8642-c83782b807c5",
  "level": 0,
  "email": "love@xray.com",
  "flow": "xtls-rprx-vision",
  "reverse": {}
}
```

`id`: string

VLESS user ID, which can be any string less than 30 bytes or a valid UUID. Custom strings and their mapped UUID are equivalent, meaning you can write the ID in the configuration file to identify the same user, e.g.,

- Write `"id": "我爱🍉老师1314"`,
- Or write `"id": "5783a3e7-e373-51cd-8642-c83782b807c5"` (this UUID is the UUID mapping of `我爱🍉老师1314`).

The mapping standard is in [VLESS UUID mapping standard: Mapping custom strings as a UUIDv5](https://github.com/XTLS/Xray-core/issues/158).

You can use the command `xray uuid -i "custom string"` to generate the UUID mapped by the custom string.

You can also use the command `xray uuid` to generate a random UUID.

`level`: number

User level, used by the connection as the local policy corresponding to this user level.

The level value corresponds to the `level` value in [policy](https://example.com/config/policy.html#policyobject). If not specified, the default is 0.

`email`: string

User email, used to differentiate the traffic of different users (reflected in logs and statistics).

`flow`: string

Flow control mode, used to choose the XTLS algorithm.

Currently, the following flow control modes are available in the inbound protocol:

- No `flow` or empty character: Use regular TLS proxy.
- `xtls-rprx-vision`: Use new XTLS mode including inner handshake random padding.

XTLS is available only in the following combinations:

- TCP+TLS/Reality: At this time, encrypted data will be directly forwarded at the underlying level (if transmitting TLS 1.3).
- VLESS Encryption: No underlying transmission restrictions; if the underlying layer does not support direct forwarding (see above), only penetrate Encryption.

`reverse`: struct

VLESS minimal reverse proxy configuration, similar to the general reverse proxy that comes with the core but simpler to configure.

If this item exists, it means connections from the user can be used to establish a reverse proxy tunnel.

Current writing:

```json
"reverse": {
  "tag": "r-outbound"
}
```

`tag` is the outbound proxy tag for this reverse proxy. Routing traffic to this outbound will forward through the reverse proxy to the connected client routing system (for client configuration, see VLESS outbound).

When multiple different connections (can be from different devices) are connected, the core will randomly select one for each request to dispatch reverse proxy data.
