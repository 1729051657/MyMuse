# 部署 MyMuse 用户服务

MyMuse 基于 nanoMuse。`deploy/mymuse/` 将已有账号中继、Web 网关和 Python 运行时接到一起。用户通过邮箱验证码创建账号，随后进入自己的持久助手。网关、中继和助手运行在同一台 Docker 宿主机上。助手工作区和设置界面仍沿用 nanoMuse。

## 服务组成 {#what-runs}

| 服务 | 职责 |
|---|---|
| Caddy | `/web/` 注册入口、`/v1/` 中继接口、`/app/` 账号控制台、`/app/admin/` 管理后台和账号域名 |
| Relay | 邮箱验证码、账号、模型额度、设备互联和对话同步 |
| Gateway | 每账号一个持久容器、域名路由和资源限制 |
| Docker socket proxy | 复用网关已有的受限 Docker API 访问 |
| Runtime image | 本地构建并包含 Chromium，网关用它创建各账号的实际容器 |

部署不构建 MobileGym，也不使用其数据集。保留 nanoMuse 的许可证和来源声明。

## 启动服务 {#start-the-service}

准备带 Docker Compose 的 Linux 服务器，将 `muse.example.com` 和 `*.agents.example.com` 指向它。80、443 端口需要直接到达 Caddy。这里的域名只是示例，部署时替换成自己的域名。

```bash
cd deploy/mymuse
cp .env.example .env
```

编辑 `.env`：

- 设置 `SITE_HOST`、`SESSION_DOMAIN`，可选填 `ACME_EMAIL`。
- 分别执行 `openssl rand -hex 32` 生成 `CLOUD_SECRET`、`CLOUD_ADMIN_TOKEN` 和 `WEB_SLUG_SALT`。升级时保留这些值。
- 设置模型服务商的 `UPSTREAM_BASE`、`UPSTREAM_KEY` 和 `CLOUD_MODELS`。填写自己的 key 可用的模型，按实际能力声明输入类型，并填写每百万 token 的人民币价格。示例模型和价格只是占位内容。`CHAT_DEFAULTS` 是可选的服务商参数 JSON，默认为空对象。
- 设置 `SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASSWORD` 和 `SMTP_FROM`。465 端口使用 SSL，其他端口使用 STARTTLS。`CODE_SENDER=smtp` 只接受邮箱账号。
- 核对普通账号的累计模型额度 `ALLOWANCE_CNY`，以及容器数量、内存和 CPU 限制。默认限制只是配置值，没有代表服务器容量的压测结论。
- 如果 `MYMUSE_EDGE_SUBNET` 与现有网络冲突，调整此配置。中继只信任该代理网络转发的访客地址，账号容器使用独立的 web 网络。

```bash
docker compose -f compose.yml config --quiet
docker compose -f compose.yml build runtime relay gateway
docker compose -f compose.yml up -d
docker compose -f compose.yml ps
```

打开 `https://muse.example.com/web/`，通过邮箱验证码注册。管理后台地址为 `https://muse.example.com/app/admin/`，使用 `CLOUD_ADMIN_TOKEN` 登录。手机和桌面客户端可按[自建说明](self-hosting.md#pointing-the-apps-at-it)，将 `https://muse.example.com` 设为自己的中继。各客户端仍独立运行智能体，记忆和任务状态不会自动与云端助手统一。

Caddy 为每个账号域名[按需申请 TLS 证书](https://caddyserver.com/docs/automatic-https#on-demand-tls)。申请前调用 `/api/web/tls?domain=…`，只允许已登记账号的准确域名。普通泛域名 DNS 记录即可，无需 DNS 服务商令牌或泛域名证书。首次访问包含证书申请等待时间。证书机构的频率限制仍然适用，尚未验证公开注册规模下的签发能力。

## 后台工作与容量 {#background-work-and-capacity}

本部署固定使用 `WEB_IDLE_STOP_S=0`。关闭浏览器后助手继续运行，运行时可以继续处理例程和目标。达到运行上限时，新账号收到 `503 web_busy`，不会通过停止已有助手来腾位置。默认账号数和运行数均为四个，应根据实测工作负载一起调整。

这解决的是容器保持运行，没有提供跨宿主机的持久调度或准时交付保证。中继会话凭据默认 30 天到期，需重新登录刷新；重新验证会使用原数据卷重建容器，可能打断正在执行的任务。模型服务故障、待审批操作、服务器停机和模型额度耗尽，仍可能导致定时任务无法完成。

## 本地验收 {#local-acceptance}

在 `.env` 中启用 `.env.example` 底部的本地配置：`muse.localhost`、`agents.localhost`、HTTP 9080 端口、回环地址绑定、`CADDY_CONFIG=Caddyfile.local` 和 `CODE_SENDER=log`。构建和启动命令相同。本地模式不发送邮件，也不申请公网证书。需要对话时配置测试模型服务，验收使用独立测试账号。

```bash
docker compose -f compose.yml logs relay
curl http://muse.localhost:9080/healthz
curl http://muse.localhost:9080/api/web/info
```

使用能将 `*.localhost` 解析到回环地址的浏览器，打开 `http://muse.localhost:9080/web/`。申请验证码后从 relay 日志读取。核对实际结果：

1. 首次登录进入独立账号域名并打开助手。
2. 上传文件、创建记忆，关闭网页再进入，两者仍可访问。
3. 注册另一个账号，无法读取前一账号的文件、记忆和聊天。
4. 重启网关后回到原账号域名，容器能被重新识别。
5. 设置一个例程并关闭浏览器，到期后检查真实结果，包括审批或模型故障。

## 数据、升级与开放注册前的工作 {#data-updates-and-remaining-launch-work}

默认配置为 `IMPROVE_DEFAULT=0`、`RECORD_TURNS=0`、`CLOUD_GEOIP=0` 和 `GITHUB_COLLECT=0`。运行时仍保存自己的聊天和文件，对话同步遵循账号设置。`/privacy` 说明了数据流向；邀请公众使用前，需补充运营者联系方式、保留周期和服务条款。

备份 relay、gateway 数据卷，各账号的 `nmw-*-data`、`nmw-*-ws`、`nmw-*-home` 数据卷，以及 `.env`。运行中的 SQLite 数据库使用[自建说明](self-hosting.md#backing-up)中的 backup API。删除中继账号不会删除助手数据卷或运营备份，这部分生命周期仍需补齐。

升级时安排维护窗口停止账号容器，构建新运行时镜像并重建 gateway、relay。已有账号容器在重建前仍使用旧镜像；用户重新登录会用原数据卷重建容器。仅更新镜像标签不会升级已经创建的助手。恢复服务前检查数据恢复及被打断的任务，升级期间保留数据卷。

本次基础部署尚未加入付费套餐、支付、会话凭据自动续期、账号数据卷删除、运行时滚动升级或跨宿主机队列。真实模型任务完成率、外发邮件和公网 HTTPS，需要在实际部署中验收后再开放注册。
