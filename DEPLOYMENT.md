# 部署

本地：Python 3.12 安装 `requirements.txt`，执行 `python -m collector demo`，再在 `site/` 执行 `npm install && npm run dev`。Vite 使用相对 base，适配 GitHub Pages 子路径。Actions 默认采集使用 self-hosted runner，静态构建使用托管 runner；Pages workflow 只部署 `site/dist`。双仓库拆分时，将 collector 保留在私有仓库，将 `public-data/v1` 和 site 构建产物发布到公开仓库。正式上线前必须人工确认余额单位、数据公开范围、学校授权和免责声明。
