# 方式二：脚本生成 sessions.jsonl

本目录为 Nitter 官方的 session 生成脚本（来自 [zedeus/nitter/tools](https://github.com/zedeus/nitter/tree/master/tools)），外加一个适合 **用 Google 登录推特** 的半自动脚本，无需再克隆 Nitter 仓库。

## 依赖

```bash
cd nitter-local
pip install -r tools/requirements.txt
```

- **用 Google 登录**：只需 `nodriver`（脚本只负责打开页面，你在浏览器里手动点「使用 Google 登录」）
- **浏览器账号密码方式**：`nodriver`、`pyotp`
- **curl 方式**：`curl_cffi`、`pyotp`（不支持 Google 登录）

## 用法

在 **nitter-local** 目录下执行：

### 用 Google 登录推特（推荐：无需密码）

```bash
cd /path/to/mask-message/nitter-local
python3 tools/create_session_manual_browser.py --append sessions.jsonl
```

会打开浏览器到 x.com 登录页，你在页面里点「使用 Google 登录」并完成授权，登录成功后脚本会自动检测 Cookie 并写入 `sessions.jsonl`，然后退出。

---

### 用户名 + 密码（支持 2FA，非 Google 登录）

```bash
cd /path/to/mask-message/nitter-local
python3 tools/create_session_browser.py 你的推特用户名 你的密码 --append sessions.jsonl
```

开启 2FA 时，把 TOTP 密钥（base32）放在密码后面：

```bash
python3 tools/create_session_browser.py 你的用户名 你的密码 你的TOTP密钥 --append sessions.jsonl
```

无头模式（不弹窗，可能更容易被风控）：

```bash
python3 tools/create_session_browser.py 你的用户名 你的密码 --append sessions.jsonl --headless
```

### curl 方式（更快，无浏览器）

```bash
cd /path/to/mask-message/nitter-local
python3 tools/create_session_curl.py 你的推特用户名 你的密码 --append sessions.jsonl
```

2FA 时同样在密码后加 TOTP 密钥。

## 生成后

脚本会把一行 JSON 追加到 `sessions.jsonl`。若之前是模板行，可先清空或备份再运行，避免重复：

```bash
# 可选：备份后重新生成
mv sessions.jsonl sessions.jsonl.bak
python3 tools/create_session_browser.py 你的用户名 你的密码 --append sessions.jsonl
```

然后重启 Nitter：

```bash
docker-compose restart nitter
```
