# Musk Tweet ETF Monitor

监控 Elon Musk 的推文，使用 LLM 分析财经相关性，查找相关 ETF 及其持仓，并通过**企业微信 / 飞书 / 钉钉**机器人发送通知。

## 功能特性

- 🐦 **推文监控** - 通过 Nitter 实例抓取多账号最新推文（默认：马斯克、特朗普）
- 🤖 **AI 分析** - 使用 LLM (DeepSeek) 分析推文的财经相关性
- 📊 **ETF 检索** - 基于关键词搜索相关 A 股 ETF
- 📈 **持仓分析** - 获取 ETF 前十大持仓并计算股票交集
- 💬 **即时通知** - 支持企业微信、飞书、钉钉机器人（可多选）

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd mask-message
```

### 2. 配置文件

复制配置模板并编辑：

```bash
cp config.example.json config.json
```

配置项说明：

```json
{
  "nitter_instances": ["https://nitter.example.com"],
  "accounts": ["elonmusk", "realDonaldTrump"],
  "wechat_webhook_url": "",
  "feishu_webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
  "feishu_keyword": "急报",
  "dingtalk_webhook_url": "",
  "dingtalk_secret": "",
  "check_interval": 300,
  "llm_config": {
    "api_base": "https://api.deepseek.com/v1",
    "api_key": "your-api-key",
    "model": "deepseek-chat"
  }
}
```

- **accounts**：要监控的 Nitter 账号列表（Twitter 用户名），如 `["elonmusk", "realDonaldTrump"]`，不填则默认只监控马斯克
- **wechat_webhook_url**：企业微信机器人 Webhook（可选）
- **feishu_webhook_url**：飞书群机器人 Webhook（可选）。在飞书群设置 → 群机器人 → 添加自定义机器人，复制 Webhook 地址
- **feishu_keyword**：若飞书机器人设置了「关键字」校验，此处填该关键字（如 `急报`），消息内容会自动带上以便发送成功
- **dingtalk_webhook_url**：钉钉群自定义机器人 Webhook（可选）
- **dingtalk_secret**：钉钉机器人若开启「加签」安全设置，在此填写 Secret

### 3. 启动服务

**Windows:**
```batch
start.bat
```

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

## 本地 Nitter（推荐）

公共 Nitter 实例常不可用。可**在本地用 Docker 自建 Nitter**，监控更稳定：

```bash
cd nitter-local
docker-compose up -d
```

在 `config.json` 中设置 `"nitter_instances": ["http://host.docker.internal:8080"]`（mask-message 跑在 Docker 时）或 `["http://localhost:8080"]`（本机直接跑时）。详见 [nitter-local/README.md](nitter-local/README.md)。

## Docker 部署

### 构建镜像

```bash
docker build -t musk-monitor .
```

### 运行容器

```bash
docker run -d \
  --name musk-monitor \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  musk-monitor
```

### 查看日志

```bash
docker logs -f musk-monitor
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 运行一次后退出，不保存已处理记录 |
| `--test-notify` | 发送测试通知后退出 |

示例：
```bash
python -m src.main --dry-run
python -m src.main --test-notify
```

## 项目结构

```
mask-message/
├── src/
│   ├── main.py          # 主程序入口
│   ├── monitor.py       # 推文监控模块
│   ├── analyzer.py      # LLM 分析模块
│   ├── market_data.py   # 市场数据模块 (AKShare)
│   ├── notifier.py      # 通知模块
│   └── utils.py         # 工具函数
├── data/                # 数据缓存目录
├── config.json          # 配置文件（需自行创建）
├── nitter-local/        # 本地 Nitter 部署（docker-compose）
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 构建文件
├── start.bat            # Windows 启动脚本
└── start.sh             # Linux 启动脚本
```

## 依赖

- Python 3.8+
- playwright - 浏览器自动化
- feedparser - RSS 解析
- openai - LLM API 调用
- akshare - A 股数据接口
- schedule - 定时任务

## 许可证

MIT License
