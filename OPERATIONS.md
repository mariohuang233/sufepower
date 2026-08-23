# 运维

首选 GitHub Actions 云端采集：在仓库 Secrets 中配置 `SUFE_EMS_TOKEN`、`SUFE_EMS_COOKIE` 和 `SUFE_EMS_REFERER`，workflow 每天北京时间 23:00 启动 `collect → export → validate`，全局 concurrency 防止重入；也可以用本地 Windows 计划任务执行同一流程。低覆盖率、认证失败或敏感字段检查失败时保留上一版。每次发布的房间余额代表当天 23:00 日终快照，历史用电量由相邻日终余额下降差分得到，不再提供“今日用电”字段。
