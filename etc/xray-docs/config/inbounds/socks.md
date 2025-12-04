# Socks

Implementation of the standard Socks protocol, compatible with [Socks 4](http://ftp.icm.edu.pl/packages/socks/socks4/SOCKS4.protocol), [Socks 4a](https://ftp.icm.edu.pl/packages/socks/socks4/SOCKS4A.protocol), Socks 5, and **HTTP**.

::: danger
**Warning**  
The Socks protocol does not encrypt transmissions and is not suitable for transmission over the public network.
:::

The more meaningful use of `Socks` inbound is to listen in a local area network or local environment to provide local services for other programs.

## InboundConfigurationObject

```json
{
  "auth": "noauth",
  "accounts": [
    {
      "user": "my-username",
      "pass": "my-password"
    }
  ],
  "udp": false,
  "ip": "127.0.0.1",
  "userLevel": 0
}
```

> `auth`: "noauth" | "password"

The authentication method for the Socks protocol supports `“noauth”` for anonymous and `“password”` for user-password methods.

When using password, HTTP requests sent to inbound will also require the same username and password.

The default value is `"noauth"`.

> `accounts`: [AccountObject]

An array where each element is a user account.

This option is only effective when `auth` is set to `password`.

The default value is empty.

> `udp`: true | false

Whether to enable UDP protocol support.

The default value is `false`.

> `ip`: address

When UDP is enabled, Xray needs to know the local machine's IP address.

The meaning of “local machine's IP address” is that the client can find the server with this IP when initiating a UDP connection. The default is the local IP when the server is connected via TCP. It should mostly work, but in some systems with NAT, this may lead to issues, requiring you to change this parameter to the correct public IP.

Warning: if there are multiple IP addresses on your machine, it will be affected by inbound UDP listening on 0.0.0.0.

> `userLevel`: number

User level, the connection will use the local policy corresponding to this user level.

The value of userLevel corresponds to the `level` value in the [policy](https://www.example.com/config/policy.html#policyobject). If not specified, it defaults to 0.

### AccountObject

```json
{
  "user": "my-username",
  "pass": "my-password"
}
```

> `user`: string

The username, of string type. Required.

> `pass`: string

The password, of string type. Required.
