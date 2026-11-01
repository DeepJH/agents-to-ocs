# agents-to-ocs：本地 AI Agent 网课题库通用桥接服务

[![GitHub](https://img.shields.io/badge/GitHub-DeepJH%2Fagents--to--ocs-blue?logo=github)](https://github.com/DeepJH/agents-to-ocs)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![OCS](https://img.shields.io/badge/OCS-Compatible-success.svg)](https://docs.ocsjs.com/)

本项目专为 **[OCS 网课助手 (Online Course Script)](https://docs.ocsjs.com/)** 打造，纯按 OCS 官方 `AnswererWrapper` 题库标准自研。全面支持将本地各种主流 **AI Agent CLI**（包括 **Google Antigravity `agy`**、**Anthropic `claude code`**、**OpenAI `codex`** 等）转化为 OCS 的私有智能题库。

- **GitHub 仓库**：[https://github.com/DeepJH/agents-to-ocs](https://github.com/DeepJH/agents-to-ocs)
- **开源许可证**：[Apache License 2.0](LICENSE)

---

## 一、 核心特性概览

- 💰 **零额外开支，不用买 API**：直接复用本地已登录的 Agent 客户端自带额度或订阅（如 Antigravity CLI 内置算力），**完全无需单独绑定外币卡购买高昂的商业 API Token，一分钱不用额外花**。
- 🛡️ **安全合规，避免反代封号**：直接驱动本地官方已登录的正式 Agent CLI 客户端，走本地官方通道，**无需使用任何第三方反代服务（Reverse Proxy），无需提取或暴露账号 Token/API Key，彻底杜绝因反代外接违反模型服务条款 (ToS) 而导致的封号与风控风险**。
- 🤖 **全 Agent 生态支持**：统一抽象底层 CLI 驱动，内置支持 **Google Antigravity (`agy`)**、**Anthropic Claude Code (`claude`)** 与 **OpenAI Codex (`codex`)**，一行命令即可随时自由切换。
- 🎯 **纯标准自研**：严格遵循 OCS `AnswererWrapper` 题库规范，无需对接任何第三方付费题库接口。
- ⚡ **无缝支持测速与探活**：原生支持 HTTP `HEAD` 请求（如 `HEAD /?t=...`），连通性秒级返回 200 OK，界面精准显示毫秒延迟。
- 🖼️ **原生多模态视觉答题**：支持接收 OCS 传回的 Base64 图片，结合视觉上下文解析公式题、图表题与纯图片选项题。
- 🛡️ **严格答案规范化**：
  - **单选题**：逐字对齐选项原文，防止模型自行附加多余序号。
  - **多选题**：严格遵循 OCS 规范，自动用半角井号 `#` 连接多个正确选项（如 `A. 正确项1#B. 正确项2`）。
  - **判断题**：建立真假同义词映射，自动对齐“对/错/正确/错误/T/F”。
  - **填空题**：多个空自动以 `#` 拼接。
- ⚡ **本地 SQLite 题库缓存**：题目解答后自动持久化到本地 `cache.db`，同一题目二次出现时**毫秒级直出**，极大节约模型额度与等待时间。
- 🚥 **并发限流与防打爆保护**：内置异步信号量队列（默认最大并发为 3），当网课平台整卷一次性并发抛出几十道题时，自动排队保护系统与 API。
- 🚀 **跨平台一键自检与参数透传**：支持 `-h/--help` 完整帮助、`-a` 切换 Agent、`-m` 选模型、`-p` 改端口等。

---

## 二、 快速上手与使用教程（核心指南）

### 1. 克隆仓库
```bash
git clone https://github.com/DeepJH/agents-to-ocs.git
cd agents-to-ocs
```

### 2. 命令行参数全览 (`-h`)
本程序的所有脚本与主程序均完整支持 CLI 参数：

```text
用法: main.py [-h] [-a {agy,claude,codex}] [-m MODEL] [-p PORT] [-H HOST]
               [-c CONCURRENCY] [-t TIMEOUT] [--no-cache] [--list-agents]
               [--list-models]

参数选项:
  -h, --help            显示命令行帮助信息并退出
  -a, --agent {agy,claude,codex}
                        指定后端 Agent CLI (默认: agy)
  -m, --model MODEL     指定推理模型名称 (留空则使用所选 Agent 的推荐默认模型)
  -p, --port PORT       指定 HTTP 服务端口 (默认: 8788)
  -H, --host HOST       指定监听地址 (默认: 127.0.0.1)
  -c, --concurrency N   设置最大并发 Agent 进程数 (默认: 3)
  -t, --timeout SECONDS 单题最大推理超时秒数 (默认: 50)
  --no-cache            禁用本地 SQLite 题库缓存
  --list-agents         列出当前系统所有支持的 Agent 类型及本地就绪状态
  --list-models         列出当前所选 Agent 的推荐模型列表
```

---

### 3. 一键启动服务示例

#### 常用启动命令：
```bash
# 1. 默认使用 Antigravity (gemini-3.8-flash-high) 极速启动
./start.sh

# 2. 切换为 Claude Code 并指定 sonnet 模型
./start.sh -a claude -m sonnet

# 3. 切换为 OpenAI Codex 并指定 o3 模型
./start.sh -a codex -m o3

# 4. 自定义服务端口为 9000，设置并发限制为 5
./start.sh -p 9000 -c 5

# 5. 查看系统内已安装的 Agent 状态
./start.sh --list-agents

# 6. 查看指定 Agent 的推荐可用模型
./start.sh -a agy --list-models
```

> **Windows 用户**：直接将上述命令中的 `./start.sh` 换成 `start.bat` 即可（如 `start.bat -a claude -m sonnet`，或直接双击 `start.bat` 默认启动）。

---

### 4. 配置 OCS 网课助手（三步完成对接）

#### 第一步：打开 OCS 题库配置面板
1. 在浏览器（已安装 Tampermonkey 或 ScriptCat 并启用 OCS 网课助手）中打开任意网课页面（如超星学习通、智慧树等）。
2. 点击页面边缘的 **OCS 悬浮图标** 展开控制面板。
3. 依次点击：**`通用` → `全局设置` → `题库配置`**。

#### 第二步：粘贴以下题库配置 JSON
将下方整段 JSON 完整粘贴到题库配置输入框中（服务启动时控制台也会实时打印）：

```json
[
  {
    "name": "Agents 智能题库",
    "homepage": "https://github.com/DeepJH/agents-to-ocs",
    "url": "http://127.0.0.1:8788/ocs",
    "method": "post",
    "type": "fetch",
    "contentType": "json",
    "responseType": "json",
    "headers": {
      "Content-Type": "application/json"
    },
    "data": {
      "title": "${title}",
      "options": "${options}",
      "type": "${type}",
      "images": {
        "handler": "return (env) => Array.isArray(env.images) ? env.images : []"
      }
    },
    "handler": "return (res) => (res && res.answer) ? [res.title, res.answer] : undefined"
  }
]
```

#### 第三步：刷新连接与开启图片题优化
1. 点击 OCS 题库面板中的 **【刷新连接】**，若配置正确将显示延迟毫秒数（如 `5ms`）。
2. 在对应网课平台（如超星）设置中，勾选开启 **【图片题优化】**，以便带图题目能正常将 Base64 发送到本地解析。
3. 保存设置，刷新做题页面即可全自动答题！

---

## 三、 工作原理与多 Agent 架构

```
┌─────────────────────────────────┐
│     网课页面 (超星/智慧树等)     │
│  运行 OCS 油猴脚本 (Tampermonkey) │
└────────────────┬────────────────┘
                 │ ① POST /ocs (携带 title, options, type, images)
                 ▼
┌────────────────────────────────────────────────────────┐
│            agents-to-ocs 本地桥接服务 (FastAPI)         │
│                   http://127.0.0.1:8788                │
│                                                        │
│  ┌────────────────────────┐   命中   ┌───────────────┐ │
│  │   本地 SQLite 缓存库     │ ──────► │ 毫秒级直出答案 │ │
│  │       (cache.db)       │         └───────────────┘ │
│  └─────────────┬──────────┘                           │
│                │ 未命中                               │
│                ▼                                      │
│  ┌────────────────────────┐                           │
│  │   并发信号量限流队列     │ (默认限流 3 并发)         │
│  └─────────────┬──────────┘                           │
│                │                                      │
│                ▼                                      │
│  ┌────────────────────────┐                           │
│  │   提示词构建与多模态解析 │ (Base64 解码为临时图片)    │
│  └─────────────┬──────────┘                           │
└────────────────┼───────────────────────────────────────┘
                 │ ② 动态调用配置的 Agent 驱动
                 ▼
┌────────────────────────────────────────────────────────┐
│                 Agent 统一抽象驱动层                   │
│                                                        │
│  ┌──────────────────┐ ┌──────────────────┐ ┌─────────┐ │
│  │ Google AGY CLI   │ │ Claude Code CLI  │ │ Codex   │ │
│  │ (agy -p ...)     │ │ (claude -p ...)  │ │ (exec)  │ │
│  └──────────────────┘ └──────────────────┘ └─────────┘ │
└────────────────┬───────────────────────────────────────┘
                 │ ③ 返回结构化答案 JSON
                 ▼
┌────────────────────────────────────────────────────────┐
│            OCS 选项匹配引擎 (ocs_matcher.py)           │
│   (单选逐字匹配 / 多选 # 连接 / 判断题归一化 / 写入缓存)  │
└────────────────┬───────────────────────────────────────┘
                 │ ④ 返回符合规范的 [题目, 答案]
                 ▼
┌─────────────────────────────────┐
│     OCS 自动匹配并填写正确答案    │
└─────────────────────────────────┘
```

### 💡 为什么直接调用本地 Agent 客户端？（省钱 + 防封号双重优势）

市面上许多所谓的“网课 AI 搜题脚本”通常采用**要求填入商业 API Key** 或 **挂载第三方反代服务器（Reverse Proxy）** 的方案，存在严重的成本与安全隐患：
1. **API 按量计费极昂贵**：如果通过各家开发者平台单独购买商业 API（如 Claude 3.7 Sonnet、GPT-4o、Gemini 等），不仅门槛高（通常需海外外币卡认证），而且多模态识图和刷题的 Token 消耗极快，成本高昂。
2. **反代外接严重违反服务条款 (ToS) 导致封号**：各大模型厂商（OpenAI、Anthropic、Google）对高频异地反代 IP、非官方接口抓包特征有极其严密的反作弊与风控机制，使用反代外接极易导致宝贵的主账号被判定异常而直接永久封禁。
3. **私有凭据外泄风险**：将个人的 API Key 或 Cookie 填入第三方脚本或中转站，存在额度被盗刷甚至账号被劫持的风险。

**`agents-to-ocs` 的核心设计哲学：**
- **零额外花费，直接白嫖客户端额度**：直接复用本地正式客户端自带的计算配额或已有订阅（如 Antigravity CLI 提供的强大推理能力），无需额外掏一分钱去买商业 API。
- **原生官方通道，彻底杜绝封号**：本项目仅充当本机内部管道，所有推理均通过本机已官方授权的正式客户端（`agy`、`claude`、`codex`）进行正常本地交互，属于标准的开发者工具调用范畴，**绝不触碰反代外接红线，不违反 ToS，彻底杜绝封号风控**。
- **纯本地回环通信**：无任何中间人代理，无任何数据上传至第三方中转服务，安全与隐私 100% 掌握在自己手中。

---

## 四、 常见问题排错 (FAQ)

### Q1: OCS 测速刷新显示 405 Method Not Allowed？
- **解答**：最新版本已为根路径 `/`、`/health`、`/ocs` 等完整注册了 `HEAD` 方法，秒回 200 OK 并显示毫秒延迟。

### Q2: Linux 提示 `error: externally-managed-environment`？
- **解答**：这是现代 Linux（Debian 12 / Ubuntu 23+）的 PEP 668 保护机制。**请直接运行 `./start.sh`**，脚本会自动创建与激活 `.venv` 虚拟环境，完全避免此报错。

### Q3: 如何查看我机器上安装了哪些 Agent？
- **解答**：执行 `./start.sh --list-agents`，脚本会自动检测系统 PATH 中的 `agy`、`claude`、`codex` 并展示详细状态。

### Q4: 提示某个 Agent 退出异常？
- **解答**：请确保该 Agent 已在本地终端中完成过登录授权：
  - `agy`：直接在终端运行 `agy` 登录
  - `claude`：在终端运行 `claude login` 登录
  - `codex`：在终端运行 `codex login` 登录

---

## 五、 开源许可证

本项目基于 [Apache License 2.0](LICENSE) 协议开源。
