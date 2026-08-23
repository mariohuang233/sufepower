# 运维

首选本地 Windows 计划任务：先在运行账户的系统环境变量中配置 `SUFE_EMS_TOKEN`、`SUFE_EMS_COOKIE` 和 `SUFE_EMS_REFERER`，再以管理员 PowerShell 执行 `.scripts\install-task.ps1`。任务每天在北京时间 00:23、04:23、08:23、12:23、16:23、20:23 执行 `collect → export → validate`，全局 Mutex 防止重入；卸载执行 `.scripts\uninstall-task.ps1`。GitHub Actions self-hosted runner 可使用同样三个 Secrets，workflow 已设置四小时 cron、concurrency 和 210 分钟超时。低覆盖率、认证失败或敏感字段检查失败时保留上一版。
