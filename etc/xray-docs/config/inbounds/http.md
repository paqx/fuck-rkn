# HTTP

The HTTP protocol.

:::danger
**Warning**

The HTTP protocol does not encrypt transmissions, making it unsuitable for transmission over the public network and more prone to being used as a bot for attacks.
:::

The more meaningful use of inbound `http` is to listen in a local network or machine environment, providing local services for other programs.

:::tip
**TIP 1**

`http proxy` can only proxy tcp protocol; protocols under udp cannot be handled.
:::

:::tip
**TIP 2**

To use a global HTTP proxy in the current session on Linux (many softwares support this setting, though some do not), use the following environment variables:

- `export http_proxy=http://127.0.0.1:8080/` (Change the address to your configured HTTP inbound proxy address)
- `export https_proxy=$http_proxy`
:::

## InboundConfigurationObject

```json
{
  "accounts": [
    {
      "user": "my-username",
      "pass": "my-password"
    }
  ],
  "allowTransparent": false,
  "userLevel": 0
}
```

> `accounts`: [AccountObject]

An array, with each element representing a user account. Default value is empty.

When `accounts` is not empty, the HTTP proxy will perform Basic Authentication on inbound connections.

> `allowTransparent`: true | false

When set to `true`, all HTTP requests are forwarded, not just proxy requests.

:::tip
**Reminder**

Misconfiguration of this option can lead to an infinite loop.
:::

> `userLevel`: number

User level, the connection uses the local policy corresponding to this user level.

The value of userLevel corresponds to the `level` value in [policy](https://example.com/config/policy.html#policyobject). If not specified, it defaults to 0.

### AccountObject

```json
{
  "user": "my-username",
  "pass": "my-password"
}
```

> `user`: string

Username, string type. Required.

> `pass`: string

Password, string type. Required.
