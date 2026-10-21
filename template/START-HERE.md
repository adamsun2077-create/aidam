# 第一次使用 Aidam

你已经有了一个空白的本地 AI 工作区。

1. 阅读 `system/AIDAM.md`，了解目录、任务执行和会话规则。
2. 填写 `system/local.json` 的 owner，在 `system/memory/MEMORY.md` 写入少量长期偏好。不要填写任何凭据。
3. 让你的 AI 先读 `AGENTS.md`、规则源和核心技能，然后一起创建第一个项目。
4. 本地检查：`python3 system/tools/aidam.py doctor .`。
5. 改文件前开始会话并声明路径，完成后提供验证、更新上下文，再结束会话。

可给 AI 的第一句话：

> 请先读取 AGENTS.md 和 system/AIDAM.md，检查工作区状态，再问我正在做什么。根据我的回答填写个人偏好，创建一个目标明确、能验证的小项目，并完成第一次会话闭环。

本目录今后会包含你的私人信息，保留在自己控制的存储中。外部连接默认关闭，按需使用自己的账号授权。模板的完整说明保留在下载的 Starter 项目 `docs/` 中。

工具不会自动安装后台任务、同步资料、提交 Git 或连接任何服务。Python 3.9+；Windows 可以使用 `py -3` 运行命令。
