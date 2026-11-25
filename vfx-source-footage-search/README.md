# vfx-source-footage-search

为视频特效训练数据找实拍原片的 Agent Skill（Claude / Codex 通用）：在 Pexels、Pixabay、Mixkit、Coverr 等免费素材站搜索，按镜头要求逐帧核查，最后给出下载链接和建议截取段。

## 开始使用

```text
请用 $vfx-source-footage-search 找 2 条 P1 原片：户外、中近景、固定机位、手上无物件、有手部和身体动作、背景不要太虚化。只给下载链接。
```

## 核查要点

固定机位 · 中近景单人 · 脸清楚 · 有身体和手部动作 · 手上无易受物理变化影响的物件 · 背景清楚且元素少 · 无第二人 · P1 必须户外 · ≥1080p，5–8 秒连续无剪辑 · 仅限成年人

## 文件

- `SKILL.md`：要求清单、素材站、搜索词、流程
- `scripts/pexels_helpers.js`：浏览器里用的缩略图墙和 6 帧抽帧工具

## 安装

将整个目录放到 `~/.codex/skills/vfx-source-footage-search/` 或 `~/.claude/skills/vfx-source-footage-search/`。
