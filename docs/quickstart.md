# 上手指南

## 第一步：创建自己的工作区

下载并解压 Starter，在解压目录打开终端。先查看 `python3 --version`，需要 3.9 或更新版本；Windows 使用 `py -3`。

```sh
python3 aidam.py init ../my-aidam
python3 aidam.py doctor ../my-aidam
```

预期结果包含 `ERROR=0`。这仅证明本地骨架完整，不能证明外部服务已连接。

下载目录是工具和模板，`my-aidam/` 是以后放私人资料的工作区。两者分开保管。初始化不会修改全局设置、安装后台任务、联网或自动创建 Git 仓库。

## 第二步：让 AI 认识你

在能操作本地文件的 AI 工具中打开 `my-aidam/`。让它先读 `AGENTS.md` 和 `system/AIDAM.md`。工具如不自动读取入口文件，可在会话首句明确要求读取；只支持聊天而不能访问文件的工具，需要人工提供必要上下文，不能自动执行本地命令。

补齐：

- `system/local.json` 的 `owner`：你的称呼。
- `system/memory/MEMORY.md`：长期偏好和经确认的事实。
- 第一个项目的目标、输入和验收标准。

直接说明目标、输入和想要的成果，例如“帮我梳理目标”“实现这个功能”“分析这份数据”。AI 根据任务选择必要能力并确认可观察的完成条件。

## 第三步：完成一次小任务

进入生成的工作区目录，再运行：

```sh
python3 system/tools/aidam.py project . --area projects --name first-project
python3 system/tools/aidam.py session start . --entry codex --claim active/projects/first-project
```

保存输出里的 `id`。声明路径后完成任务，更新项目和区域的 `.context.md`。结束时使用真实 ID：

```sh
python3 system/tools/aidam.py session finish . --id YOUR_SESSION_ID --summary "本次做了什么；如何验证；还有什么未完成"
```

日志进入 `system/memory/sessions/日期/`，使用运行电脑的本地时区。路径声明只发现参与本协议的会话冲突，不会阻止其他程序直接改文件。

## 常用命令

以下命令都在自己的工作区根目录执行：

| 需求 | 命令 |
|---|---|
| 检查骨架 | `python3 system/tools/aidam.py doctor .` |
| 近三天摘要 | `python3 system/tools/aidam.py context recent .` |
| 定位项目 | `python3 system/tools/aidam.py context assemble . --task "关键词"` |
| 新建分析项目 | `python3 system/tools/aidam.py project . --area data --name analysis-demo` |
| 开始修改 | `python3 system/tools/aidam.py session start . --entry codex --claim active/data/analysis-demo` |
| 写入日志并释放声明 | `python3 system/tools/aidam.py session finish . --id YOUR_SESSION_ID --summary "结果、证据、待办"` |

`entry` 只是实际入口的标识，可填 `codex`、`claude-code`、`workbuddy`、`grok-bot` 或自己的名称。填写名称不会连接对应产品。

## 接下来

先按 [虚构演练](walkthrough.md) 完成一次闭环，再按 [连接器说明](connectors.md) 接入一个真正需要的服务。不要一次配置所有连接。

备份自己的工作区时选择本机备份或自己控制的私有存储；初始化附带的 `.gitignore` 会默认忽略私人资料，不能把一次 Git 提交当成完整备份。

上下文命令只读、不联网；摘要截取日志非空行合并后的前240字符，默认最多20条，超量会标记截断。项目定位按目录名和 `.context.md` 中的字面关键词匹配，返回路径，不是语义搜索。多候选需核对，未命中时扩大关键词检索并回读原文。
