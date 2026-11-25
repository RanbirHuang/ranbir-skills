# ranbir-skills
Ranbir's own-created skills

## social-post-copy：通用社媒文案

为不同品牌和项目生成 Caption、中文翻译、Hashtag 和可追溯来源，支持单条素材与 CSV/Excel 批量策划表。

- [技能入口](social-post-copy/SKILL.md)
- [快速开始与安装](social-post-copy/README.md)
- [完整使用说明](social-post-copy/references/USAGE.md)
- [项目配置模板](social-post-copy/assets/project-profile.example.json)
- [输入及交付字段](social-post-copy/references/DATA_CONTRACT.md)

### 安装

下载或克隆仓库后，将 `social-post-copy/` 整个目录放到 `~/.codex/skills/social-post-copy/`；如设置了 `CODEX_HOME`，使用其下的 `skills/social-post-copy/`。保留技能目录内所有文件，同名目录已存在时先比较本地修改。

安装后在新项目聊天中调用：

```text
请用 $social-post-copy，根据本项目要求和素材生成 Caption、中文翻译及 Hashtag。
```

每条至少提供发布平台、目标语言和素材事实。品牌词、目标市场、账号风格及标签要求可直接在消息中说明，也可使用项目配置模板。

## vfx-source-footage-search：特效原片素材查找

按镜头要求（固定机位、中近景、手上无物件、有动作、背景清楚）在免费素材站找实拍原片，逐帧核查后给出下载链接。

- [技能入口](vfx-source-footage-search/SKILL.md)
- [快速开始与安装](vfx-source-footage-search/README.md)
- [浏览器核查工具](vfx-source-footage-search/scripts/pexels_helpers.js)
