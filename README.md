# SUFE 电量观察站

这是上海财经大学宿舍电量公开查询与趋势平台的安全隔离实现。它不需要用户注册，不提供充值或任何写接口；私有采集端保存 Token 和事实库，公开站点只读取脱敏静态 JSON。

快速演示：`python -m collector demo`，`python scripts/validate_public.py`，然后 `cd site; npm install; npm run dev`。Python 测试使用 `pytest -q`，前端测试使用 `npm run test`，构建使用 `npm run build`。真实采集需要先取得正式只读授权，再在受限 runner 中设置 `SUFE_EMS_TOKEN`；请先阅读 [AUTHORIZATION.md](AUTHORIZATION.md)，不要把 Token 发到聊天或提交到仓库。程序只允许清单内只读 GET，不会主动调用真实学校接口。

如果已有浏览器请求中的 Bearer 凭据，可在本机使用 `python scripts/collect_with_bearer.py` 隐藏粘贴并执行一次采集；该凭据仍必须属于获授权账号，并不等同于学校对长期自动采集的正式许可。

如果 EMS 依赖完整浏览器请求上下文，可在浏览器选择“复制为 cURL”，只在本机保存为临时文本，然后运行 `python scripts/collect_from_curl.py C:\\临时目录\\request.txt`。脚本只接受 EMS 的 GET 请求，读取完毕后应立即删除临时文件；不要把该文件内容发送到聊天或提交到 Git。

详细边界见 [ARCHITECTURE.md](ARCHITECTURE.md)、[DATA_CONTRACT.md](DATA_CONTRACT.md)、[PRIVACY.md](PRIVACY.md)、[OPERATIONS.md](OPERATIONS.md) 与 [DEPLOYMENT.md](DEPLOYMENT.md)。
