# social-post-copy

为不同品牌和项目生成社交媒体 Caption、中文翻译、Hashtag 及来源说明的 Codex Skill。支持单条文字素材和 CSV/Excel 批量策划表。

适合 TikTok、Instagram 等用户指定的平台。品牌、市场、语言、账号风格、标签数量和输入列名都由当前项目决定。

## 开始使用

安装后，在项目聊天中输入：

```text
请用 $social-post-copy 制作文案。
发布平台：TikTok
文案语言：英语
素材内容：填写本条素材中实际出现的人物、动作和画面。
项目或品牌：填写品牌名称；没有可省略。
目标市场：美国
必须包含的标签：填写指定标签；没有可省略。
```

平台、语言和素材事实是必要输入。其他选项及批量任务示例见[完整使用说明](references/USAGE.md)。

单条输出包含 Caption、中文翻译、Hashtag、可复制贴文和复核状态。批量默认输出 Excel、CSV、证据工作簿和运行报告。

## 安装与项目配置

下载或克隆本仓库，将包含 `SKILL.md` 的完整目录放到 `~/.codex/skills/social-post-copy/`。如果设置了 `CODEX_HOME`，则使用其下的 `skills/social-post-copy/`。保留 `agents/`、`assets/` 和 `references/`，同名技能已存在时先比较本地改动。

安装完成后，新开项目聊天并调用 `$social-post-copy`。

有固定品牌规则时，将[配置模板](assets/project-profile.example.json)复制到目标项目根目录，命名为 `post-copy.project.json`，再填写该项目的实际规则。不必为每个新项目复制一份技能。

## 文件入口

- [技能指令](SKILL.md)：Codex 执行流程与判断规则。
- [使用说明](references/USAGE.md)：填写方法、调用示例、安装和适用边界。
- [数据约定](references/DATA_CONTRACT.md)：字段映射、配置含义、证据等级和输出格式。
- [项目配置模板](assets/project-profile.example.json)：品牌、语言、语气及标签规则。
- [输入 CSV 表头](assets/input-template.csv)：批量素材的可选起点。

## 默认规则与限制

- 最多 5 个相关标签，可少于 5 个；需要精确数量时明确指定。
- 不预置品牌标签或 `#fyp`，默认不生成 `@` 账号。
- 默认简体中文翻译及 0–2 个 Emoji，可按项目调整。
- 普通草稿可基于用户文字；当前热门程度需要另外查证，来源不充分时标记需复核。
- 默认不分析视频、音频或图片，也不自动发布或发送结果。

本仓库是由 Codex 读取执行的技能包，不附带独立命令行生成程序。无需固定 API 服务或指定模型；实时研究与表格导出取决于当前运行环境的可用工具。结构、配置示例和内部链接已校验，未验证完整的真实联网批量流程。
