# PiliPlus AltStore Source

[PiliPlus](https://github.com/bggRGjQaUbCoE/PiliPlus)（使用 Flutter 开发的 BiliBili 第三方客户端）的 **AltStore / SideStore 源**，由 GitHub Actions 自动同步上游 Releases，无需人工维护。

灵感与格式参考 [ChouChiu/Kazumi-AltStore-Source](https://github.com/ChouChiu/kazumi-altstore-source)。

## 添加源

在 AltStore / SideStore 的 **Sources（源）** 页面点击 `+`，填入以下任一地址：

```
https://raw.githubusercontent.com/Pyramid-RJ/PiliPlus-altstore-source/main/generated/apps.json
```

```
https://raw.githubusercontent.com/Pyramid-RJ/PiliPlus-altstore-source/main/alt_store.json
```

两个地址内容完全一致，只是文件名风格不同（`alt_store.json` 为经典命名，`generated/apps.json` 与 Kazumi 源一致）。

## 功能

- ⏱️ **自动更新**：GitHub Actions 每 6 小时拉取一次 [PiliPlus Releases](https://github.com/bggRGjQaUbCoE/PiliPlus/releases)，发现新的 iOS 构建后自动更新源文件并以 `github-actions[bot]` 身份提交；也可以在 Actions 页面手动触发（`workflow_dispatch`）。
- 📜 **完整版本历史**：收录每个 Release 的更新日志、下载直链、文件大小与构建号（buildVersion）。
- 🔔 **更新通知**：最新 Release 会生成一条 News 通知。
- 🖼️ 图标与截图直接引用上游仓库资源。

## 安装说明

- 源中收录的是上游发布的**未签名 ipa**，AltStore / SideStore 安装时会自动使用你的 Apple ID 重签：
  - 免费 Apple ID：证书 7 天有效，到期需重新安装（可在设备上用 AltStore 刷新）；
  - Apple Developer 账号或 SideStore 配合脉冲/热刷新等方案可长期使用。
- 最低系统要求：**iOS 15.0**。

## 工作原理

```
GitHub Actions (cron 每 6 小时 / 手动触发)
        │
        ▼
scripts/generate.py  ──拉取──>  api.github.com/repos/bggRGjQaUbCoE/PiliPlus/releases
        │                      （过滤 draft / prerelease / 无 ipa 的 Release）
        ▼
生成 generated/apps.json 与 alt_store.json
        │
        ▼
检测到变化 → 以 github-actions[bot] 提交并推送
```

生成脚本仅使用 Python 标准库（`urllib` / `json` / `re`），Actions 的 ubuntu 环境无需安装任何依赖。

## 免责声明

本仓库仅生成并托管指向上游 Releases 的索引信息，不修改、不重打包任何应用；所有资源版权归 PiliPlus 原作者及 Bilibili 所有。请于下载后 24 小时内自行评估使用风险，因使用本项目产生的任何问题由使用者自行承担。
