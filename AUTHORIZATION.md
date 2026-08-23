# 授权与 Token 接入

## 先取得什么授权

本项目只能在获得上海财经大学相关部门或 EMS 系统管理员明确许可后运行。建议授权内容至少写明：允许读取哪些只读接口；允许覆盖哪些校区、楼栋和房间；采集频率为每 4 小时一次；默认并发为 1、请求间隔不少于 1 秒；公开数据字段和保留期限；出现异常时的停止和撤销方式；以及谁负责确认余额单位和隐私边界。

不要使用抓包得到的他人 Cookie、设备号、账户号或未经允许的 Token，也不要尝试调用登录、短信、绑定、解绑、充值、支付等接口。本项目只允许 `GET` 只读接口，授权被撤回或返回 401/403 时应立即停止。

## Token 如何提供

不要把 Token 发给 Codex、写进代码、命令行参数、Git、截图、Issue 或前端构建产物。推荐在 self-hosted runner 上配置环境变量：

Windows PowerShell 当前会话临时配置：

```powershell
$env:SUFE_EMS_TOKEN = "在本机安全输入的授权 Token"
python scripts/check_token.py
python -m collector collect --slot now
```

长期任务建议由 runner 服务账号通过系统环境变量或受限凭据管理器提供，而不是保存在项目目录。变量应只对采集进程可见，普通用户不应有读取权限。Token 轮换时先停止定时任务，更新 Secret，执行检查，再恢复任务。

当前默认请求速率为 10 QPS，硬上限也是 10 QPS；程序会在 401、403、429 或服务端异常时立即停止。正式长期运行前仍应让接口方确认该速率。

如果浏览器请求同时依赖 `Authorization`、Cookie 和 Referer，不要复制整段 Request 到聊天里。推荐运行 `python scripts/collect_with_bearer.py`，在本机隐藏粘贴 Bearer 和 Cookie，并输入 Referer；凭据只传给一次采集子进程，不会写入文件、命令行参数或日志。浏览器 Bearer 可能绑定账号、Cookie、IP 或短时会话，能访问不等于已经获得长期自动采集授权。

## 如何验证是否授权成功

先执行 `python scripts/check_token.py`，它只输出 Token 是否存在、长度范围和是否含有明显空白，不输出 Token 内容。随后执行 `python -m collector collect --slot now`；如果返回 401/403，说明 Token 无效、过期或没有对应只读权限，程序会在不重试的情况下停止。不要为了“验证”去调用写接口。

## 正式上线前的人工确认

请让授权方确认：Token 所属账号有权读取目标宿舍范围；EMS 返回的余额单位；公开房间目录是否合规；历史数据保存期限；以及网站免责声明。只有这些内容确认后，才应把 `runs-on: self-hosted` 的 GitHub Actions 采集任务打开。
