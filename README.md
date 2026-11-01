# AGY to OCS：基于 Antigravity CLI 的智能网课题库桥接服务

[![GitHub](https://img.shields.io/badge/GitHub-DeepJH%2Fagy--to--ocs-blue?logo=github)](https://github.com/DeepJH/agy-to-ocs)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![OCS](https://img.shields.io/badge/OCS-Compatible-success.svg)](https://docs.ocsjs.com/)

本项目专为 **[OCS 网课助手 (Online Course Script)](https://docs.ocsjs.com/)** 打造，纯按 OCS 官方 `AnswererWrapper` 题库标准自研。通过桥接本地 **Google Antigravity CLI (`agy`)**，将 `gemini-3.8-flash-high` 等高精度多模态大语言模型直接包装为 OCS 的本地私有智能题库。

- **GitHub 仓库**：[https://github.com/DeepJH/agy-to-ocs](https://github.com/DeepJH/agy-to-ocs)
- **开源许可证**：[Apache License 2.0](LICENSE)

---

## 一、 核心特性概览

- 🎯 **纯标准自研**：严格遵循 OCS `AnswererWrapper` 通信与选项匹配规范，无需注册或依赖第三方付费题库接口。
- ⚡ **无缝支持测速与探活**：原生支持 HTTP `HEAD` 请求（如 `HEAD /?t=...`），连通性秒级返回 200 OK，界面精准显示毫秒延迟。
- 🖼️ **原生多模态视觉答题**：支持接收 OCS 传回的 Base64 图片，由 `gemini-3.8-flash-high` 结合视觉上下文解析公式题、图表题与纯图片选项题。
- 🛡️ **严格答案规范化**：
  - **单选题**：逐字对齐选项原文，防止模型自行附加多余序号。
  - **多选题**：严格遵循 OCS 规范，自动用半角井号 `#` 连接多个正确选项（如 `A. 正确项1#B. 正确项2`）。
  - **判断题**：自动对齐“对/错/正确/错误/T/F”。
  - **填空题**：多个空自动以 `#` 拼接。
- ⚡ **本地 SQLite 题库缓存**：题目解答后自动持久化到本地 `cache.db`，同一题目二次出现时**毫秒级直出**，极大节约模型额度与等待时间。
- 🚥 **并发限流与防打爆保护**：内置异步信号量队列（默认最大并发为 3），当网课平台整卷一次性并发抛出几十道题时，自动排队保护系统与 API。
- 🚀 **跨平台一键自检与启动**：自动检测环境、创建虚拟环境、安装依赖并一键启动。

---

## 二、 快速上手与使用教程（核心指南）

### 1. 克隆仓库
```bash
git clone https://github.com/DeepJH/agy-to-ocs.git
cd agy-to-ocs
```

### 2. 一键启动服务

#### 🐧 Linux / macOS 环境（一键脚本）
```bash
chmod +x start.sh
./start.sh
```
> **自动规避 PEP 668**：现代 Linux（Debian 12+ / Ubuntu 23+）默认开启 PEP 668 限制全局 pip。该脚本会自动创建 `.venv` 隔离环境并调用虚拟环境 pip，**全程无需 root / sudo 权限**。

#### 🪟 Windows 环境（一键双击）
直接双击运行 [start.bat](start.bat) 即可。脚本会自动检查系统 Python、创建 `.venv` 并完成依赖安装与拉起。

#### 🛠️ 手动安装运行（面向开发者）
```bash
python3 -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows PowerShell / CMD

pip install -r requirements.txt
python main.py
```

服务启动成功后，将监听在 `http://127.0.0.1:8788`。

---

### 3. 配置 OCS 网课助手（三步完成对接）

#### 第一步：打开 OCS 题库配置面板
1. 在浏览器（已安装 Tampermonkey 或 ScriptCat 并启用 OCS 网课助手）中打开任意网课页面（如超星学习通、智慧树等）。
2. 点击页面边缘的 **OCS 悬浮图标** 展开控制面板。
3. 依次点击：**`通用` → `全局设置` → `题库配置`**。

#### 第二步：粘贴以下题库配置 JSON
将下方整段 JSON 完整粘贴到题库配置输入框中（服务启动时控制台也会实时打印）：

```json
[
  {
    "name": "AGY 智能题库 (gemini-3.8-flash-high)",
    "homepage": "https://antigravity.google",
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

## 三、 工作原理与架构图

```
┌─────────────────────────────────┐
│     网课页面 (超星/智慧树等)     │
│  运行 OCS 油猴脚本 (Tampermonkey) │
└────────────────┬────────────────┘
                 │ ① POST /ocs (携带 title, options, type, images)
                 ▼
┌────────────────────────────────────────────────────────┐
│              AGY to OCS 本地桥接服务 (FastAPI)           │
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
                 │ ② 执行 agy -p --model gemini-3.8-flash-high
                 ▼
┌─────────────────────────────────┐
│     Google Antigravity CLI      │
│             (agy)               │
└────────────────┬────────────────┘
                 │ ③ 模型推理返回结构化 JSON
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

---

## 四、 高级配置与环境变量

程序支持通过修改 [config.py](config.py) 或通过系统环境变量进行无入侵定制：

| 环境变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `OCS_HOST` | `127.0.0.1` | 服务监听的 IP 地址 |
| `OCS_PORT` | `8788` | 服务监听端口 |
| `OCS_MODEL` | `gemini-3.8-flash-high` | 推理使用的模型（可选 `gemini-3.8-flash-low`、`claude-sonnet-4-6` 等） |
| `OCS_EFFORT` | `""` (留空) | 推理深度（若模型名已自带 high/medium 则留空） |
| `OCS_MAX_CONCURRENCY` | `3` | 最大并发调起 `agy` 进程数，防止本地负载过高或 API 限流 |
| `OCS_TIMEOUT` | `50` | 单题最大推理等待秒数（OCS 硬超时为 60s） |
| `OCS_ENABLE_CACHE` | `true` | 是否启用 SQLite 题库缓存持久化 |
| `OCS_DB_PATH` | `cache.db` | 本地 SQLite 缓存数据库文件存放路径 |

#### 快速切换低延迟模型示例：
```bash
# 使用极速模型启动服务
OCS_MODEL=gemini-3.8-flash-low ./start.sh
```

---

## 五、 常见问题排错 (FAQ)

### Q1: OCS 测速刷新显示 405 Method Not Allowed？
- **解答**：最新版本已为根路径 `/`、`/health`、`/ocs` 等完整注册了 `HEAD` 方法，请确保拉取最新代码运行，即可秒回 200 OK 并显示毫秒延迟。

### Q2: Linux 提示 `error: externally-managed-environment`？
- **解答**：这是现代 Linux（Debian 12 / Ubuntu 23+）的 PEP 668 保护机制。**请直接运行 `./start.sh`**，脚本会自动创建与激活 `.venv` 虚拟环境，完全避免此报错。

### Q3: 提示 `agy 退出异常` 或 `未找到 agy 命令`？
- **解答**：
  1. 请检查终端执行 `which agy`（Linux）或 `where agy`（Windows）是否能找到该可执行程序。
  2. 若未登录，请先在终端直接输入 `agy` 并完成初次身份验证授权。

### Q4: 为什么部分题目首次作答较慢？
- **解答**：
  1. 默认采用的 `gemini-3.8-flash-high` 拥有极高的推理深度与准确率，推理耗时通常在 10~25 秒左右。
  2. **答过一次的题目会自动存入 SQLite 题库**，下次在同门课程做作业或期末考试遇到完全相同的题目时，服务将在 **10 毫秒内秒级返回**。
  3. 若追求极速搜题，可设置环境变量 `OCS_MODEL=gemini-3.8-flash-low` 启动，耗时可缩短至数秒。

---

## 六、 开源许可证

本项目基于 [Apache License 2.0](LICENSE) 协议开源。
