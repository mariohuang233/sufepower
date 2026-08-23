# 部署

本地：Python 3.12 安装 `requirements.txt`，执行 `python -m collector demo`，再在 `site/` 执行 `npm install && npm run dev`。Vite 使用相对 base，适配 GitHub Pages 子路径。Actions 默认采集使用 self-hosted runner，静态构建使用托管 runner；Pages workflow 只部署 `site/dist`。双仓库拆分时，将 collector 保留在私有仓库，将 `public-data/v1` 和 site 构建产物发布到公开仓库。正式上线前必须人工确认余额单位、数据公开范围、学校授权和免责声明。
# GitHub Actions 自动采集

自动采集 workflow 位于 `.github/workflows/collector.yml`，使用已批准的 self-hosted runner 执行只读 EMS 请求。它按北京时间每天 00:23、04:23、08:23、12:23、16:23、20:23 运行，默认固定为 10 QPS；每次运行会将数据写入 runner 本地 `var/sufeelec.db`，导出并校验脱敏后的 `public-data/v1`，然后只提交公开数据，Pages workflow 会继续负责部署站点。

在仓库 Settings → Secrets and variables → Actions → New repository secret 中配置 `SUFE_EMS_TOKEN`，如真实请求需要完整浏览器上下文，再配置 `SUFE_EMS_COOKIE` 和 `SUFE_EMS_REFERER`。三者都只能作为 GitHub Secrets 保存，不要写入 workflow、命令行参数、Issue、artifact 或聊天记录；凭据失效时应撤销并重新生成。`SUFE_EMS_TOKEN` 为空时 workflow 会在发起请求前失败。

首次启用前需要在仓库 Settings → Actions → General 将 Workflow permissions 设为允许读写 repository contents，并确保 self-hosted runner 已在线且具备 Python 3.12、PowerShell 和访问 EMS 的网络权限。之后可在 Actions → private collection → Run workflow 手动执行；手动执行默认也会发布，若只想验证采集和校验，可将 `publish` 设为 false。每次运行保留 7 天私有 SQLite/日志诊断 artifact，公开数据中不会包含这些内容。

GitHub Actions 的 cron 使用 UTC，workflow 已换算为上海时区；GitHub 可能对整点附近的 scheduled workflow 延迟，手动执行可用于立即验证。采集失败、HTTP 401/403/429 或公开数据校验失败时不会推送 `public-data`。
