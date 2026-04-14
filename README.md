# anime-video-production

AI漫剧制作系统 · 即梦 Seedance 2.0 全流水线 Claude Code Skill

## 功能

- 故事规划 → 素材生成 → 视频提示词 → 转场 → 合集拼接
- 真相文件系统（防角色漂移/场景穿越）
- 三层规则栈 + 集数门禁
- 串行提交规范（含实测并发限制）

## 安装

```bash
# 添加为 marketplace
claude plugin marketplace add Egber1t/anime-video-production

# 安装 skill
claude plugin install anime-video-production@Egber1t
```

## 要求

- 即梦高级会员（¥649/月）
- `~/bin/dreamina.exe` CLI 已登录
- ffmpeg（拼接用）

## 使用

在 Claude Code 中输入 `/anime-video-production` 即可启动。
