# 本地 Nitter 部署

供 mask-message 使用的自建 Nitter 实例，与公共 Nitter 实例相比更稳定、不受限流影响。

## 启动

```bash
cd nitter-local
docker-compose up -d
```

## 验证

浏览器打开：http://localhost:8080/elonmusk  
若能看到马斯克时间线（或 Nitter 的提示页），说明运行正常。

## 让 mask-message 使用本机 Nitter

在 **mask-message** 的 `config.json` 中，将 `nitter_instances` 改为本地地址：

- **mask-message 跑在 Docker 里**：填 `["http://host.docker.internal:8080"]`
- **mask-message 跑在本机**：填 `["http://localhost:8080"]`

保存后重启 mask-message 容器（或进程）。

## 关于 Session（2024+）

当前 Nitter 从 Twitter 拉取内容需要 **Twitter 会话凭证**，否则会报 “Instance has no auth tokens”。本目录下 `sessions.jsonl` 已有一行模板，**必须把占位符换成真实 Cookie** 后重启才可正常抓推文。

### 方式一：浏览器里复制 Cookie（最快）

1. 浏览器登录 [x.com](https://x.com)。
2. 按 F12 → **Application**（或「存储」）→ **Cookies** → 选 `https://x.com`。
3. 找到并复制这两个 Cookie 的值：
   - `auth_token`
   - `ct0`
4. 编辑本目录下的 `sessions.jsonl`，把那一行里的占位符替换掉：
   - `"请替换为浏览器中x.com的auth_token"` → 你的 `auth_token` 值
   - `"请替换为浏览器中x.com的ct0"` → 你的 `ct0` 值
   - `"你的推特用户名"` → 你的用户名（可选，便于排查）
5. 保存后执行：`docker-compose restart nitter`（或先 down 再 up -d）。

### 方式二：用本目录脚本生成（已集成官方脚本）

无需克隆 Nitter 仓库，在本项目内即可完成。

1. 安装依赖（在 **nitter-local** 目录下）：
   ```bash
   cd nitter-local
   pip install -r tools/requirements.txt
   ```
2. 任选一种方式生成并写入 `sessions.jsonl`：
   - **用 Google 登录推特**（推荐）：脚本只打开登录页，你在浏览器里点「使用 Google 登录」即可，登录成功后脚本自动抓 Cookie。
     ```bash
     python3 tools/create_session_manual_browser.py --append sessions.jsonl
     ```
   - **用户名 + 密码**（支持 2FA）：
     ```bash
     python3 tools/create_session_browser.py 你的推特用户名 你的密码 --append sessions.jsonl
     ```
     若开启 2FA，在密码后加 TOTP 密钥。
   - **curl 方式**（更快，无浏览器，不支持 Google 登录）：
     ```bash
     python3 tools/create_session_curl.py 你的推特用户名 你的密码 --append sessions.jsonl
     ```
3. 重启 Nitter：`docker-compose restart nitter`

更多选项与说明见 **tools/README.md**。官方文档：[Creating session tokens](https://github.com/zedeus/nitter/wiki/Creating-session-tokens)。

## 镜像说明

- **Mac M1/M2（ARM64）**：已默认使用 `zedeus/nitter:latest-arm64`。
- **x86**：在 `docker-compose.yml` 中将镜像改为 `zedeus/nitter:latest`。

## 停止

```bash
cd nitter-local
docker-compose down
```
