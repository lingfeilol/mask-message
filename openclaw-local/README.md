# OpenClaw Gateway 容器化

用 Docker 跑 OpenClaw Gateway，等价于本机执行 `openclaw gateway --port 18789 --verbose`，便于统一用容器管理。

## 首次使用

1. **复制环境变量（可选）**
   ```bash
   cp .env.example .env
   ```
   如需用已有配置，在 `.env` 里把 `OPENCLAW_CONFIG_DIR` 指向你的 `~/.openclaw`（例如 `/Users/你的用户名/.openclaw`），`OPENCLAW_WORKSPACE_DIR` 指向对应 workspace。

2. **若没有现成配置，先建目录**
   ```bash
   mkdir -p config workspace
   ```
   首次启动后需做一次 onboarding（见下）。

3. **启动**
   ```bash
   docker-compose up -d
   ```

4. **查看状态**
   ```bash
   docker-compose ps
   docker-compose logs -f openclaw-gateway
   ```

## 首次配置（onboarding）

若 `config` 为空，Gateway 可能要求先完成配置。用 CLI 容器跑向导：

```bash
docker compose --profile cli run --rm openclaw-cli onboard
```

按提示选择「Local gateway」等。完成后重启网关：

```bash
docker-compose restart openclaw-gateway
```

## 控制台 / Dashboard

- 浏览器打开：http://localhost:18789  
- 需要 token 时，获取链接：
  ```bash
  docker compose --profile cli run --rm openclaw-cli dashboard --no-open
  ```
- 若提示需配对设备：
  ```bash
  docker compose --profile cli run --rm openclaw-cli devices list
  docker compose --profile cli run --rm openclaw-cli devices approve <requestId>
  ```

## 常用 CLI（与官方一致）

在 `openclaw-local` 目录下执行：

```bash
# 状态
docker compose --profile cli run --rm openclaw-cli status

# 健康检查
docker compose --profile cli run --rm openclaw-cli gateway health --url ws://127.0.0.1:18789

# 通道配置（如 Telegram）
docker compose --profile cli run --rm openclaw-cli channels add --channel telegram --token "<token>"
```

## 停止

```bash
docker-compose down
```

## 说明

- 使用预构建镜像 `alpine/openclaw:latest`，无需克隆 OpenClaw 仓库或本地 build。
- 端口 18789（WebSocket）、18790（bridge）与官方及你之前的本地命令一致。
- 配置与 workspace 通过卷挂载，重启或重建容器后仍会保留。
