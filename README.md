# Aidam

**把自己的文件夹，变成 AI 能持续协作的工作台。**

Aidam 是一套以本地知识库为核心的个人 AI 工作方式。用统一的目录、规则、技能和记忆，让不同 AI 工具接着做事，让成果留在自己手里。

你拿到的是可运行的空白模板、五个核心技能和一套接入方法。填入自己的资料、选择自己的 AI 工具，就能开始。外部服务按需授权。

## 先跑起来

准备 Python 3.9 或更高版本，以及一个能读写本地文件的 AI 工具。下载本项目 ZIP 并解压，在项目目录运行：

```sh
python3 aidam.py init ../my-aidam
python3 aidam.py doctor ../my-aidam
```

Windows 可使用 `py -3` 替换 `python3`。目标必须是新目录或空目录。

打开生成的 `my-aidam/`，阅读 `START-HERE.md`，让你的 AI 执行这个开场任务：

> 请先读取 AGENTS.md 和 system/AIDAM.md，检查工作区状态，再问我正在做什么。根据我的回答填写 owner、长期记忆和第一个项目；修改前声明路径，完成后提供验证并写会话日志。

[完整上手指南](docs/quickstart.md) · [虚构演练](docs/walkthrough.md)

## 你能复用什么

| 部分 | 作用 |
|---|---|
| 本地知识库 | 文件与成果留在自己的目录，方便阅读、备份和迁移 |
| 三角色分工 | CEO 处理商业问题，VibeCoder 做工程，Data Analyst 分析数据 |
| 单一规则源 | 工具入口共同读取 `system/AIDAM.md` |
| 跨会话记忆 | 长期事实与单次会话日志分开，减少重复说明 |
| 路径声明 | 多工具接力时发现目录重叠；不自动锁定编辑器 |
| 完成前验证 | 结论附证据，测试与未完成事项写清楚 |
| 通用连接器 | 按需接入文档、数据平台和企业协作系统 |

## 工作区长什么样

```text
my-aidam/
├── AGENTS.md                  入口指引
├── CLAUDE.md                  入口指引
├── START-HERE.md              第一次使用
├── system/
│   ├── AIDAM.md               唯一规则源
│   ├── local.json             自己的本机配置
│   ├── memory/                私人记忆与会话日志
│   ├── skills/                通用核心技能
│   ├── bridges/               自己的连接器说明
│   ├── runtime/               会话与路径声明
│   └── tools/aidam.py          本地工具
├── active/
│   ├── projects/              开发项目
│   ├── data/                  数据分析
│   ├── content/               内容创作
│   ├── clients/               客户项目
│   └── skills/                开发中的技能
├── operations/                长期运营资料和通用产出
├── archive/                   手动确认后归档
└── tmp/                       临时文件
```

## 逐步搭建

1. **基础版**：一个本地目录＋一个 AI 工具，先做到项目、记忆、日志闭环。
2. **连接版**：按实际需求接入飞书、公司知识库或数据平台，每个服务使用自己的账号。
3. **接力版**：加入第二个工具，通过本地文件、路径声明和交接单接力。云端同步单独评估。

模板只要求 Python 标准库，无需额外安装软件包。AI 工具与外部服务的订阅、可用性和权限由使用者自行选择。

## 阅读顺序

- [上手与常用命令](docs/quickstart.md)
- [架构与协作逻辑](docs/architecture.md)
- [核心技能与扩展](docs/skills.md)
- [连接器配置边界](docs/connectors.md)
- [隐私与安全分享](docs/privacy.md)

## 验证与分享

```sh
python3 -m unittest discover -s tests -v
python3 aidam.py share --output ../aidam-starter.zip
```

分享命令只读取 `share-manifest.json` 与程序内同时列明的文件，生成 SHA-256 校验清单；不会导出你初始化后的工作区。自动扫描仅辅助检查，发布前请人工审阅文件清单。

版本：Starter 0.1.0。模板是对一套个人工作方式的通用化重写，不包含原作者的记忆、项目、聊天附件或账号配置。MIT 许可适用于本仓库原创文件；外部工具与服务遵循各自条款。
