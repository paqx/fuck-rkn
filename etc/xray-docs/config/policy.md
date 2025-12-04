# Local Policy

Local policies allow setting different user levels and corresponding policy settings, such as connection timeout settings. Each connection processed by Xray corresponds to a user, and different policies are applied based on the user level.

## PolicyObject

`PolicyObject` corresponds to the `policy` item in the configuration file.

```json
{
  "policy": {
    "levels": {
      "0": {
        "handshake": 4,
        "connIdle": 300,
        "uplinkOnly": 2,
        "downlinkOnly": 5,
        "statsUserUplink": false,
        "statsUserDownlink": false,
        "statsUserOnline": false,
        "bufferSize": 4
      }
    },
    "system": {
      "statsInboundUplink": false,
      "statsInboundDownlink": false,
      "statsOutboundUplink": false,
      "statsOutboundDownlink": false
    }
  }
}
```

> `level`: map{string: [LevelPolicyObject](#levelpolicyobject)}

A set of key-value pairs, each key is a numeric string (as required by JSON), such as `"0"`, `"1"`, etc. The quotes are required, and this number corresponds to the user level. Each value is a [LevelPolicyObject](#levelpolicyobject).

:::tip
Each inbound and outbound proxy can now set user levels, and Xray will apply different local policies based on the actual user level.
:::

> `system`: [SystemPolicyObject](#systempolicyobject)

Xray system-level policies.

### LevelPolicyObject

```json
{
  "handshake": 4,
  "connIdle": 300,
  "uplinkOnly": 2,
  "downlinkOnly": 5,
  "statsUserUplink": false,
  "statsUserDownlink": false,
  "bufferSize": 10240
}
```

> `handshake`: number

The handshake time limit when establishing a connection, in seconds. The default value is `4`. If the handshake phase exceeds this time when an inbound proxy processes a new connection, the connection is interrupted.

> `connIdle`: number

The idle time limit for a connection, in seconds. The default value is `300`. If no data is transferred (including uplink and downlink) during the `connIdle` time while processing a connection, the connection is interrupted.

> `uplinkOnly`: number

The time limit after the downlink is closed, in seconds. The default value is `2`. When the server (such as a remote website) closes the downlink, the outbound proxy will interrupt the connection after waiting for the `uplinkOnly` time.

> `downlinkOnly`: number

The time limit after the uplink is closed, in seconds. The default value is `5`. When the client (such as a browser) closes the uplink, the inbound proxy will interrupt the connection after waiting for the `downlinkOnly` time.

:::tip
In HTTP browsing scenarios, `uplinkOnly` and `downlinkOnly` can be set to `0` for more efficient connection closure.
:::

> `statsUserUplink`: true | false

When `true`, uplink traffic statistics for all users at the current level are enabled.

> `statsUserDownlink`: true | false

When `true`, downlink traffic statistics for all users at the current level are enabled.

> `statsUserOnline`: true | false

When `true`, online user count statistics for the current level are enabled. (Online criterion: connection activity within 20 seconds)

> `bufferSize`: number

The internal buffer size for each request, in KB. Note that multiple requests may be multiplexed on the same connection, such as when using mux.cool or GRPC, meaning their buffer pools are independent even if they share the same underlying connection.

When the internal buffer exceeds this value, writing occurs only after the buffer is sent and reduced to or below this value.

Note that for a UDP request, if a write attempt occurs when the buffer is full, the operation will not block but will be **discarded**. Setting this too low or to 0 may lead to unexpected bandwidth waste.

Defaults:

- On ARM, MIPS, MIPSLE platforms, the default is `0`.
- On ARM64, MIPS64, MIPS64LE platforms, the default is `4`.
- On other platforms, the default is `512`.

Defaults can be set through the environment variable `XRAY_RAY_BUFFER_SIZE`. Note that in the environment variable, the unit is MB (setting it to 1 is equivalent to setting it to 1024 in the config).

### SystemPolicyObject

```json
{
  "statsInboundUplink": false,
  "statsInboundDownlink": false,
  "statsOutboundUplink": false,
  "statsOutboundDownlink": false
}
```

> `statsInboundUplink`: true | false

When `true`, uplink traffic statistics for all inbound proxies are enabled.

> `statsInboundDownlink`: true | false

When `true`, downlink traffic statistics for all inbound proxies are enabled.

> `statsOutboundUplink`: true | false

When `true`, uplink traffic statistics for all outbound proxies are enabled.

> `statsOutboundDownlink`: true | false

When `true`, downlink traffic statistics for all outbound proxies are enabled.
