# 独立发布安排

用户于 2026-10-23 指定发布到 leohal-hue，作为独立项目，与上海影史地图使用不同仓库。

- 账号：`leohal-hue`
- 独立仓库名：`chinese-cinema-history`
- 网站内容目录：`docs/`
- 网站：https://leohal-hue.github.io/chinese-cinema-history/
- 仓库：https://github.com/leohal-hue/chinese-cinema-history
- 网页、正式资料表与维护脚本已提交；网站已公开响应 HTTP 200。
- 原始 Excel 与原始记录快照暂保留本机，待用户单独确认是否公开。

## 首次发布

1. 使用 leohal-hue 账号新建公开仓库 `chinese-cinema-history`。
2. 把本项目文件上传到仓库根目录，包含 `.github/`、`docs/`、`data/`、`scripts/`、`sources/` 及说明文件。不要把整个压缩包作为唯一文件上传，也不要把文件放入上海影史地图仓库。
3. 当前设置为 Settings → Pages → Deploy from a branch → `main` → `/docs`。
4. 提交生成后的网页文件，等待 Pages 部署完成，再验证实际地址。
5. 验证线上检索、补充备注、资料下载和页面跳转；将实际地址写回 README。

后续数据修改先运行 `python3 scripts/build.py`，把 CSV 与生成后的网页数据一同提交到 `main`，随后自动发布网站。普通读者可通过仓库 Issue 提供依据。

发布通过 leohal-hue 的已登录 Chrome 会话完成。现有 GitHub 插件账号不同，不用于向本仓库直接写入。
