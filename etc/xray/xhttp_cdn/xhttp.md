# First

Short answer: yes. XHTTP is exactly for “HTTP-only middleboxes/CDNs” and is the best way to run Xray through a CDN whose IPs are whitelisted by your ISP.

What to use
- Start with XHTTP in packet-up mode (most compatible with “static-file CDNs” that buffer requests).
- If your CDN supports gRPC streaming, switch to XHTTP stream-up for better upstream performance.
- If your CDN supports H3 to the edge, you can try client ALPN=h3; the CDN can still talk H1/H2 to your origin, which XHTTP supports.

Typical topology
Client —TLS(H2/H3)→ CDN —(H1/H2/“whatever it has”)→ Nginx/Caddy on VPS —→ Xray (xhttp inbound)

You do NOT need TCP passthrough. TLS terminates at the CDN, and the CDN forwards HTTP to your origin. XHTTP is designed to survive this.

Server setup (minimal)
1) Xray inbound (VLESS + XHTTP) on localhost. Use a long random path. Keep security “none” behind Nginx.
- Example (server):
  {
    "inbounds": [{
      "tag": "in-vless-xhttp",
      "listen": "127.0.0.1",
      "port": 10000,
      "protocol": "vless",
      "settings": { "clients": [{ "id": "<uuid>" }] },
      "streamSettings": {
        "network": "xhttp",
        "security": "none",
        "xhttpSettings": { "path": "/<very-random-path>" }
      }
    }],
    "outbounds": [{ "protocol": "freedom" }]
  }

2) Nginx in front, serving your CDN-connected hostname, forwarding only that path to Xray:
- Option A (recommended to start; packet-up, works on almost all CDNs):
  server {
    listen 443 ssl http2;
    server_name your.domain;
    ssl_certificate ...; ssl_certificate_key ...;

    location /<very-random-path>/ {
      proxy_http_version 1.1;
      proxy_request_buffering off;     # stream request to backend
      proxy_buffering off;             # stream response back
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-For $remote_addr;
      proxy_pass http://127.0.0.1:10000;
    }
  }

- Option B (for stream-up; needs CDN gRPC support + Nginx grpc_pass):
  server {
    listen 443 ssl http2;
    server_name your.domain;
    ssl_certificate ...; ssl_certificate_key ...;

    location /<very-random-path>/ {
      grpc_set_header Host $host;
      grpc_pass grpc://127.0.0.1:10000;
    }
  }

Notes:
- If your CDN only talks HTTP to origin, make Nginx listen on 80 (and set the CDN origin to HTTP). Packet-up still works. For stream-up, many CDNs need HTTP/2 to origin (gRPC), which some do support.
- Do not put the path in a common prefix. Use something unguessable.

Client setup (connects to CDN)
Use your CDN edge IP as address (if you have an “optimized IP”), and put the CDN hostname in SNI/host.

- Example (client):
  {
    "outbounds": [{
      "tag": "proxy",
      "protocol": "vless",
      "settings": {
        "vnext": [{
          "address": "CDN_EDGE_IP_OR_DOMAIN",
          "port": 443,
          "users": [{ "id": "<uuid>" }]
        }]
      },
      "streamSettings": {
        "network": "xhttp",
        "security": "tls",
        "tlsSettings": {
          "serverName": "your.domain",
          "alpn": ["h2"]              // try ["h3"] later if your CDN supports H3
        },
        "xhttpSettings": {
          "host": "your.domain",      // host header; priority: host > serverName > address
          "path": "/<very-random-path>",
          "mode": "packet-up"         // start here; switch to "stream-up" if your CDN supports gRPC
        }
      }
    }],
    "inbounds": [{ "port": 1080, "listen": "127.0.0.1", "protocol": "socks" }]
  }

When to use stream-up
- Enable on CDN: gRPC support (or equivalent).
- Change client xhttpSettings.mode to "stream-up".
- Switch Nginx location to grpc_pass (Option B above).
- XHTTP already adds gRPC-like headers by default. CF and some CDNs also need “gRPC on edge” enabled.
- Many CDNs kill idle HTTP streams around 100s. XHTTP server has scStreamUpServerSecs padding by default (20–80s random); leave it on.

H3 over CDN
- If your CDN supports H3 at the edge, set client ALPN ["h3"]. The CDN can downshift to H1/H2 to your origin; your Xray server doesn’t need to listen on QUIC.

Practical tips
- If you use a CDN “optimized IP”, set client address=that IP and tlsSettings.serverName=your.domain.
- Leave XHTTP defaults (xPaddingBytes, XMUX). They’re already randomized to reduce fingerprinting.
- For Cloudflare-like CDNs:
  - Turn on gRPC (for stream-up).
  - If you see idle disconnects, keep default scStreamUpServerSecs.
- If Nginx “doesn’t pass” stream-up, use grpc_pass; if packet-up has issues, ensure proxy_request_buffering off and proxy_buffering off.
- Don’t enable mux.cool with XHTTP.

Troubleshooting
- Set Xray client log to info to see: HTTP version in use (H2/H3), mode (packet-up/stream-up), host, and whether it’s working through the CDN.
- 403/404 from CDN: path mismatch or CDN rule blocking; ensure exact path with trailing slash and that caching is disabled for it.
- 524/timeout: your CDN may buffer POST to completion; try packet-up (default) and reduce POST size via scMaxEachPostBytes if needed; or switch to stream-up with gRPC if supported.
- If using “optimized IP”, wrong SNI/host will break it—double-check serverName/host.

Advanced: split up/down (optional)
- XHTTP supports “downloadSettings” so upload and download can go through different front doors (e.g., v4 vs v6, different CDN PoPs). Useful but not required for your use case.

Bottom line
- Yes, you can run Xray through your CDN; XHTTP was built for this.
- Start with: Nginx + Xray xhttp inbound, client H2 + packet-up to CDN IP with SNI=your domain.
- If the CDN supports gRPC streaming, switch to stream-up for better upstream speed.

# Second

Short answer: not in one hop. REALITY cannot be used “through” an HTTP CDN that terminates TLS. If the CDN only does HTTP(S) proxying for static/large files, it will terminate your TLS, so a REALITY handshake won’t reach your server intact. You must pick one:
- Use XHTTP over TLS to the CDN (works; SNI can be the CDN’s whitelisted name).
- Or connect directly with REALITY (no CDN in the middle).

Given your constraints (IP and SNI whitelists), the practical solution is:
- Client connects to the CDN edge IP with TLS and SNI=the CDN’s whitelisted hostname.
- The CDN forwards HTTP to your origin (Nginx/Caddy → Xray xhttp inbound).
- Transport = XHTTP (mode packet-up first; switch to stream-up if your CDN supports gRPC/H2 to origin).

How to wire it

Client (to CDN)
- address: 151.236.122.216 (your CDN edge IP)
- tls SNI (serverName): lyyv9pz13u.a.trbcdn.net (the whitelisted name)
- streamSettings:
  - network: xhttp
  - security: tls
  - tlsSettings: serverName=lyyv9pz13u.a.trbcdn.net, alpn ["h2"] (try ["h3"] later if edge supports H3)
  - xhttpSettings:
    - host: choose based on your CDN routing:
      - If CDN routes by Host header to your origin: set host to the hostname you configured on the CDN for your origin.
      - If CDN lets you set a fixed origin for the property: you can keep host=lyyv9pz13u.a.trbcdn.net and just have CDN route /yourpath to your origin.
    - path: /your-very-random-path
    - mode: "packet-up" to start; switch to "stream-up" only if the CDN supports gRPC/H2 to origin.

Server
- Put Xray behind Nginx/Caddy. Xray inbound: VLESS + xhttp on 127.0.0.1:10000, security "none", path=/your-very-random-path.
- Nginx for packet-up:
  - proxy_request_buffering off
  - proxy_buffering off
  - proxy_http_version 1.1
  - location /your-very-random-path/ → proxy_pass http://127.0.0.1:10000;
- If you later use stream-up (only if CDN gRPC is enabled), switch that location to grpc_pass grpc://127.0.0.1:10000;

About your CDN “Static” vs “Large files”
- Both can work with packet-up. “Large files” profiles that favor ranged/chunked transfer are usually friendlier to long streaming responses. You don’t need CDN compression; XHTTP already sets headers to avoid caching and to stream.

Why REALITY can’t be combined with the CDN here
- REALITY requires the client’s TLS to reach the REALITY server intact. An HTTP CDN terminates TLS and makes a new HTTP request to your origin. That breaks REALITY by design.
- You can use REALITY only on direct connections (security:"reality"). If you must pass the ISP’s SNI whitelist, you could pick a whitelisted SNI for REALITY and go direct to your VPS IP, but then you lose the CDN’s whitelisted IP advantage (and will likely be throttled).

Optional tricks (if your CDN allows them)
- Same-domain fronting: Some CDNs accept SNI=a.example.com while Host=c.example.com and still route by Host. If your ISP requires SNI=lyyv9pz13u.a.trbcdn.net, keep SNI exactly that, and set xhttp host to the hostname your CDN maps to your origin. Many CDNs require SNI and Host to be in the same cert; test with curl before committing.
- Optimized/anycast IPs: keep address=the IP, serverName=the whitelisted hostname.

Bottom line
- Use XHTTP over TLS to the CDN with SNI=the CDN’s whitelisted hostname. That satisfies both the IP and SNI checks and works with your “static/large file” CDN.
- REALITY cannot run through this CDN; it’s an either-or choice. If your goal is to pass the ISP checks and keep good speed, stick with XHTTP via CDN (packet-up first; stream-up if your CDN supports gRPC).

# Third

Yes. You have a few practical ways to “pin” the CDN to a whitelisted edge while still sending SNI=the CDN hostname.

Quickest for one-off tests
- curl/wget: force the IP while keeping SNI via --resolve
  curl --http2 -L -o /dev/null -w '%{speed_download}\n' \
    --resolve lyyv9pz13u.a.trbcdn.net:443:151.236.122.216 \
    https://lyyv9pz13u.a.trbcdn.net/path/to/file

System/browser-wide (may not affect DoH apps)
- /etc/hosts: map the CDN hostname to the whitelisted IP
  lyyv9pz13u.a.trbcdn.net 151.236.122.216
Note: some apps ignore hosts via DoH; Xray does not if you set address directly or override DNS inside Xray.

Best for Xray: pin IP while keeping SNI
- Set address to the whitelisted IP, and tls serverName to the CDN hostname. Example:
  "outbounds": [{
    "tag": "cdn",
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "151.236.122.216",
        "port": 443,
        "users": [{ "id": "<uuid>" }]
      }]
    },
    "streamSettings": {
      "network": "xhttp",
      "security": "tls",
      "tlsSettings": { "serverName": "lyyv9pz13u.a.trbcdn.net", "alpn": ["h2"] },
      "xhttpSettings": { "host": "lyyv9pz13u.a.trbcdn.net", "path": "/<your-path>", "mode": "packet-up" }
    }
  }]

Pin to a small vetted list (fallback/rotation)
Option A: override DNS inside Xray so the CDN name only resolves to your allowed edges:
- Keep address as the domain and add:
  "dns": {
    "hosts": {
      "lyyv9pz13u.a.trbcdn.net": [
        "151.236.122.216",
        "151.236.122.218"
      ]
    },
    "disableCache": true
  }
Xray will only use those IPs; if the first fails, it will try the next.

Option B: multiple outbounds + balancer (random/failover across fixed IPs):
- Define one outbound per whitelisted IP, then a balancer:
  "outbounds": [
    { "tag": "cdn-1", ... "address": "151.236.122.216", ... },
    { "tag": "cdn-2", ... "address": "151.236.122.218", ... }
  ],
  "routing": {
    "balancers": [{ "tag": "cdn-bal", "selector": ["cdn-1","cdn-2"] }],
    "rules": [{ "type": "field", "balancerTag": "cdn-bal", "port": "0-65535" }]
  }
This avoids public DNS entirely and rotates among IPs you trust.

Operational tips
- Keep SNI and xhttp host set to the CDN hostname that your ISP whitelists.
- If the CDN sometimes removes an edge IP, maintain 2–3 known-good IPs in your list to avoid outages.
- If your CDN offers “optimized IP” or region-specific edge endpoints, use those; ask support for a static or region-pinned edge if possible.
- If IPv6 ranges are also whitelisted, consider an IPv6-pinned outbound and prefer v6 on the client.

This way you always hit a whitelisted subnet while preserving the required SNI.

# Fourth

Here’s a clean, CDN-friendly setup adapted to your case:
- CDN supports H2/H3 at the edge, but you don’t have gRPC. So use XHTTP in packet-up mode (most compatible with “HTTP CDN”).
- Origin behind Nginx; Nginx forwards only a secret path to Xray and returns 403 for anything else.
- Client connects to the CDN edge IP with SNI=lyyv9pz13u.a.trbcdn.net. Start with ALPN h2, then test h3.

1) Xray server (behind Nginx)
Pick ONE of these (TCP or Unix socket). TCP is simpler.

TCP variant:
{
  "inbounds": [{
    "tag": "in-vless-xhttp",
    "listen": "127.0.0.1",
    "port": 10000,
    "protocol": "vless",
    "settings": {
      "clients": [{ "id": "<YOUR-UUID>" }],
      "decryption": "none"
    },
    "streamSettings": {
      "network": "xhttp",
      "security": "none",
      "xhttpSettings": {
        "path": "/<very-random-path>",
        "mode": "packet-up"
      }
    }
  }],
  "outbounds": [{ "protocol": "freedom" }]
}

Unix socket variant (optional):
{
  "inbounds": [{
    "tag": "in-vless-xhttp",
    "listen": "/dev/shm/xrxh.sock,0666",
    "protocol": "vless",
    "settings": {
      "clients": [{ "id": "<YOUR-UUID>" }],
      "decryption": "none"
    },
    "streamSettings": {
      "network": "xhttp",
      "security": "none",
      "xhttpSettings": {
        "path": "/<very-random-path>",
        "mode": "packet-up"
      }
    }
  }],
  "outbounds": [{ "protocol": "freedom" }]
}

2) Nginx origin
Your CDN can do H2/H3 with the client even if your origin is plain HTTP. Use the HTTP variant unless your CDN forces HTTPS-to-origin.

A. HTTP origin (recommended: no cert needed)
server {
    listen 80 default_server;
    server_name _;

    # Deny everything by default
    location / { return 403; }

    # Forward ONLY your XHTTP path to Xray (TCP variant)
    location ^~ /<very-random-path>/ {
        proxy_http_version 1.1;
        proxy_request_buffering off;
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;

        proxy_pass http://127.0.0.1:10000;
    }

    # If you used the Unix socket variant instead, replace the last line with:
    # proxy_pass http://unix:/dev/shm/xrxh.sock:;
}

B. HTTPS origin (only if CDN requires TLS to origin)
- Generate a self-signed cert (if CDN allows ignoring validation), or install a real one.

server {
    listen 443 ssl http2 default_server;
    server_name _;

    ssl_certificate     /etc/nginx/self.crt;
    ssl_certificate_key /etc/nginx/self.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    location / { return 403; }

    location ^~ /<very-random-path>/ {
        proxy_http_version 1.1;
        proxy_request_buffering off;
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;

        proxy_pass http://127.0.0.1:10000;
        # or: proxy_pass http://unix:/dev/shm/xrxh.sock:;
    }
}

Notes
- Do NOT use grpc_pass: your CDN doesn’t advertise gRPC; packet-up is the safe mode.
- You don’t need HTTP/3 on origin; H3 is only between client and CDN.
- Keep the trailing slash in Nginx location and use the same path in Xray.

3) Xray client (to CDN)
- Pin to a whitelisted CDN edge IP if needed, but keep SNI = lyyv9pz13u.a.trbcdn.net.
- Start with H2; then test H3 by changing ALPN.

{
  "inbounds": [{
    "listen": "127.0.0.1",
    "port": 1080,
    "protocol": "socks",
    "settings": { "udp": true }
  }],
  "outbounds": [{
    "tag": "cdn",
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "151.236.122.216",         // whitelisted CDN IP (or keep the CDN hostname here)
        "port": 443,
        "users": [{ "id": "<YOUR-UUID>", "encryption": "none" }]
      }]
    },
    "streamSettings": {
      "network": "xhttp",
      "security": "tls",
      "tlsSettings": {
        "serverName": "lyyv9pz13u.a.trbcdn.net",  // SNI the ISP whitelists
        "alpn": ["h2"]                            // start with H2; later test ["h3","h2"]
      },
      "xhttpSettings": {
        "host": "lyyv9pz13u.a.trbcdn.net",        // Host header; safe to match SNI
        "path": "/<very-random-path>",            // same as server
        "mode": "packet-up"                       // most compatible with HTTP CDNs
      }
    }
  }],
  "routing": {
    "rules": [{
      "type": "field",
      "ip": ["geoip:private"],
      "outboundTag": "direct"
    }]
  }
}

If you need to rotate among a few whitelisted CDN IPs
- Either set address to the domain and add Xray DNS hosts:
  "dns": { "hosts": { "lyyv9pz13u.a.trbcdn.net": ["151.236.122.216","151.236.122.218"] } }
- Or create multiple outbounds (one per IP) and balance between them.

When/if to try stream-up
- Only if your CDN confirms gRPC/H2 to origin is supported. Then:
  - Change server xhttpSettings.mode to "stream-up".
  - In Nginx, replace the proxy_pass block with a grpc_pass block.
  - Keep scStreamUpServerSecs default on server (XHTTP will keep idle alive).
  - Many CDNs require explicitly enabling gRPC; if you don’t see that option, stick to packet-up.

Why not REALITY/Vision here
- Your HTTP CDN terminates TLS; REALITY/Vision require end-to-end TLS. They won’t pass through such CDNs.

This setup satisfies:
- Client→CDN: TLS with H2 now, H3 later (you control with ALPN).
- CDN→origin: plain HTTP (or HTTPS if required).
- Only your secret path is proxied to Xray; all other requests get 403.