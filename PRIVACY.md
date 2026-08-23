# 隐私边界

公开目录不允许出现账户号、设备号、账户名称、手机号、用户名、订单号、支付渠道、Token、Authorization、Cookie、原始 API JSON 或精确在线状态。Token 只从 `SUFE_EMS_TOKEN` 环境变量读取，私有 SQLite、原始响应与日志位于 `var/` 并被 gitignore；原始响应清理命令默认保留七天。浏览器收藏仅存 localStorage，不上传。

生产建议 `PUBLISH_INTRADAY_HISTORY=false`，仅发布 latest 与每日历史；即便如此，Git 历史中的旧内容不能声称被真正删除，公开仓库应采用合适的历史清理和访问策略。
