# Run MyMuse for your users

MyMuse builds on nanoMuse. The deployment under `deploy/mymuse/` brings together the existing account relay, web gateway and Python runtime. An e-mail code creates an account and opens that account's persistent assistant. The gateway, relay and assistants run on one Docker host. The browser assistant still uses nanoMuse's existing workspace and settings UI.

## What runs {#what-runs}

| Service | Responsibility |
|---|---|
| Caddy | Registration at `/web/`, the relay at `/v1/`, account console at `/app/`, administrator console at `/app/admin/`, and account hostnames |
| Relay | E-mail codes, accounts, model allowance, devices and conversation sync |
| Gateway | One persistent container per account, host routing and resource limits |
| Docker socket proxy | The gateway's existing restricted Docker API access |
| Runtime image | Built locally with Chromium; the gateway creates the actual account containers from it |

No MobileGym build or dataset is used. The project retains nanoMuse's licence and attribution.

File links in replies, including `/workspace/` and `sandbox:/workspace/` paths, open the existing workspace viewer when they refer to a file generated in that conversation. Saved conversations keep the same file links when reopened.

The chat's **Browser** button opens the hosted browser directly for navigation, clicking, typing and login. It uses Chromium inside the account's container, independently of desktop hands. The default memory limit is 2 GB per assistant; make sure the Docker host has room for the number of browsers you run. A container limit alone does not reserve host memory.

## Start the service {#start-the-service}

Use a Linux server with Docker Compose. Point `muse.example.com` and `*.agents.example.com` to it. Ports 80 and 443 must reach Caddy directly. Use hostnames of your own; these are examples.

```bash
cd deploy/mymuse
cp .env.example .env
```

Edit `.env`:

- Set `SITE_HOST`, `SESSION_DOMAIN` and optionally `ACME_EMAIL`.
- Generate `CLOUD_SECRET`, `CLOUD_ADMIN_TOKEN` and `WEB_SLUG_SALT` separately with `openssl rand -hex 32`. Keep them stable across updates.
- Set your model provider's `UPSTREAM_BASE`, `UPSTREAM_KEY` and `CLOUD_MODELS`. Use a model available under your key, disclose its actual input modalities and set its actual prices in CNY per million tokens. The example's model and prices are placeholders. `CHAT_DEFAULTS` is an optional provider-specific JSON object, empty by default.
- Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` and `SMTP_FROM`. Port 465 uses SSL; other ports use STARTTLS. `CODE_SENDER=smtp` accepts e-mail accounts only.
- Review `ALLOWANCE_CNY`, the lifetime model allowance for an ordinary account, and the container counts and resource limits. The shipped limits are configuration values, not a measured server capacity.
- Change `MYMUSE_EDGE_SUBNET` if it overlaps an existing network. The relay trusts forwarded visitor addresses only from this proxy network; account containers use the separate web network.

```bash
docker compose -f compose.yml config --quiet
docker compose -f compose.yml build runtime relay gateway
docker compose -f compose.yml up -d
docker compose -f compose.yml ps
```

Open `https://muse.example.com/web/`. Register with an e-mail code. To visit the administrator console, open `https://muse.example.com/app/admin/` and use `CLOUD_ADMIN_TOKEN`. Mobile and desktop clients can use `https://muse.example.com` as their custom relay, following [self-hosting.md](self-hosting.md#pointing-the-apps-at-it). They still run their own agents; memory and task state are not automatically unified with the cloud assistant.

Caddy uses [on-demand TLS](https://caddyserver.com/docs/automatic-https#on-demand-tls) for each account hostname. Before issuing a certificate it calls `/api/web/tls?domain=…`, which accepts only a registered account's exact hostname. Ordinary wildcard DNS is sufficient; no DNS-provider token or wildcard certificate is needed. The first visit includes certificate issuance. Certificate-authority rate limits still apply; certificate issuance at public-registration scale has not been validated.

## Search and public pages {#search-and-public-pages}

New assistants use the existing You.com search connector by default, without a search API key. Set `MYMUSE_SEARCH_PROVIDER` to another supported provider before creating assistants, or change an existing account under Connections → Web search. Saved account choices take precedence. Anonymous search has provider limits; use your own search API key or SearXNG instance for a public service.

If public pages are refused as private hosts, inspect their DNS answers inside an assistant. Some host proxies return Fake-IP addresses in `198.18.0.0/15` or `2001:2::/48`. These addresses are not public, so the tools refuse them. Keep that check enabled and use real DNS answers.

This stack includes an optional CoreDNS resolver that forwards public DNS over TLS with certificate-name verification. First inspect the web network with `docker network inspect mymuse-web`, then choose an unused address in its subnet and set these in `.env`:

```dotenv
COMPOSE_PROFILES=encrypted-dns
MYMUSE_DNS_IP=an-unused-address-in-the-web-network
```

Replace the placeholder with an actual IP address. With another project name, inspect its `<project>-web` network. Run `docker compose -f compose.yml up -d dns gateway`. New assistant containers receive this DNS server through `WEB_DNS_SERVERS`; existing containers need recreation, normally by signing in again. Their data volumes remain. Docker continues resolving private service names such as `relay`. The resolver does not expose a host port; its upstreams are configured in `Corefile` using the [CoreDNS forward plugin](https://coredns.io/plugins/forward/).

## Background work and capacity {#background-work-and-capacity}

This stack fixes `WEB_IDLE_STOP_S=0`. Closing a browser leaves its assistant running so the runtime can keep handling routines and goals. When the running limit is reached, another account gets `503 web_busy`; an existing assistant is not stopped to make room. Account and running counts both default to four. Increase them together after measuring your workload.

This keeps containers running; it does not provide a durable multi-host scheduler or a delivery-time guarantee. The relay session key expires after 30 days by default. Sign in again to refresh it; reauthentication recreates the container around the same volumes and may interrupt an active task. Provider failures, missing approvals, server downtime and exhausted model allowance can still prevent a scheduled task from completing.

A refreshed hosted session gets a new Hub device ID so it does not claim an ID still held by the previous session. Restarting the same session keeps its ID. The account hostname, chat history, files and model choice are kept. Previous device entries can remain offline in Devices.

## Local acceptance {#local-acceptance}

In `.env`, enable the local settings at the bottom of `.env.example`: `muse.localhost`, `agents.localhost`, HTTP port 9080, loopback bindings, `CADDY_CONFIG=Caddyfile.local`, and `CODE_SENDER=log`. Keep the same build and start commands. This setup writes codes to the relay log and does not request public certificates. Configure a test model provider if you need chat; use a separate account for acceptance.

To test real e-mail delivery with the same local HTTP setup, set `CODE_SENDER=smtp` and fill in `SMTP_*`. Use the provider's SMTP authorization code as `SMTP_PASSWORD` when required. Recreate the relay with `docker compose -f compose.yml up -d --no-deps relay`, then request a code on the registration page and read it in the recipient's mailbox. The link in that message still points to the local service.

```bash
docker compose -f compose.yml logs relay
curl http://muse.localhost:9080/healthz
curl http://muse.localhost:9080/api/web/info
```

Open `http://muse.localhost:9080/web/` in a browser that resolves `*.localhost` to loopback. Request a code and read it in the relay log or mailbox, according to `CODE_SENDER`. Check these visible results:

1. A first sign-in reaches a separate account hostname and opens the assistant.
2. Upload a file, create a memory, close the page and return. Both remain available.
3. Register a second account. It cannot read the first account's files, memory or chat.
4. Restart the gateway, then return to the same account hostname. Its container is recovered.
5. Set up a routine and close the browser. Check its actual result after it is due, including any approval or provider failure.

## Data, updates and remaining launch work {#data-updates-and-remaining-launch-work}

The stack defaults to `IMPROVE_DEFAULT=0`, `RECORD_TURNS=0`, `CLOUD_GEOIP=0` and `GITHUB_COLLECT=0`. The runtime still keeps its own chats and files, and conversation sync follows the account's setting. `/privacy` explains the data paths; add your operator contact, retention policy and service terms before inviting public users.

Back up the relay and gateway volumes, every account's `nmw-*-data`, `nmw-*-ws` and `nmw-*-home` volumes, and `.env`. Use SQLite's backup API for a live database, as in [self-hosting.md](self-hosting.md#backing-up). Account deletion in the relay does not remove assistant volumes or operator backups. That lifecycle remains launch work.

To update, stop account containers during a maintenance window, build the new runtime image and recreate the gateway and relay. Existing account containers retain their original image until recreated; users signing in again recreates their containers around the same volumes. Updating the image tag alone does not upgrade already-created assistants. Verify recovery and interrupted work before reopening access. Do not remove volumes during an update.

This initial deployment does not add paid plans, payments, automatic session-key renewal, account-volume deletion, rolling runtime upgrades or a multi-host queue. Real-provider task completion, outbound e-mail and public HTTPS require acceptance in your deployment before opening registration.
