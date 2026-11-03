# 通用 Caption / Hashtag Skill 使用说明

技能名：`social-post-copy`。用途是把单条文字素材或批量策划表变成社媒发布文案、中文翻译、Hashtag 和来源记录，供不同品牌及新项目复用。它延续了旧 PixVerse 流程中的素材核对、逐条差异化、语言本地化和证据分级，但品牌规则由各项目提供。

## 与旧版的区别

- 品牌词不再固定为 `#pixverse`，也不默认加 `#fyp`；首位、末位、必选标签均由当前项目指定。
- 默认最多 5 个相关标签，有几项依据就用几项；需要“恰好 5 个”时明确要求或在配置中设 `exact`。必选标签也计入总数。
- 支持自定义列名和项目定位，不把 PixVerse 生产表的字段当成所有项目标准。
- 默认 Emoji 0–2 个、不带 `@` 账号、翻译为简体中文；都可由项目或本轮要求调整。
- 由 Codex 直接执行，不调用 `pixverse_post_copy.py`，不自动继承旧缓存、历史文案、模板链接、凭据或品牌信息。
- 不需要用户提供固定搜索 API/生成 API 的 Key。实时研究仍需要当前环境有可用搜索或连接器；没有时会标记限制，不能把离线草稿称为已验证热门文案。
- 旧版 skill 保留，PixVerse 项目仍可继续使用。旧版 `config.json` / `curated_copy.json` 不与本配置直接兼容；迁移时只搬明确仍有效的规则。

## 最快开始：直接给任务

在新项目聊天中调用：

```text
请用 $social-post-copy 为这个新项目生成发布文案。
平台：Instagram
目标市场：美国
目标语言：英语
账号定位：分享家庭烘焙过程，语气轻松。
素材事实：展示手工揉面过程，没有成品画面。
要求：一条 Caption、中文翻译、最多 4 个相关 Hashtag。
没有品牌必选词，不使用 Emoji。
```

不用先建 JSON。没有提供足够事实时，技能会询问影响写作的缺项；不会自动沿用旧项目品牌或假定某个国家只使用一种语言。

批量调用：

```text
请用 $social-post-copy 处理本项目的 campaign.xlsx。
项目规则在 post-copy.project.json。
处理所有内容工作表，每条输出一份文案，不修改原文件。
逐条给出 Caption、中文翻译、Hashtag 和来源；不能核实的标记需复核。
```

要先审首个热点时，加上“只处理第一个热点的全部记录”。没有指定范围则按完整输入处理；有歧义的辅助表或筛选范围会先确认。

## 新项目有固定规则时

将本技能的 `assets/project-profile.example.json` 复制到**新项目根目录**，命名为 `post-copy.project.json`，填入当前项目规则。技能不会自动在每个项目写配置，也不会修改全局模板。

例如某个新品牌需要固定标签，可以填写：

```json
{
  "project_name": "烘焙内容项目",
  "brand_name": "DemoBake",
  "account_positioning": "分享家庭烘焙过程",
  "default_platform": "Instagram",
  "default_market": "US",
  "default_language": "en",
  "translation_language": "zh-CN",
  "tone": "轻松、具体，不夸大成果",
  "allow_mentions": false,
  "emoji": {"min": 0, "max": 1},
  "forbidden_terms": ["guaranteed results"],
  "hashtags": {
    "count_mode": "at_most",
    "count": 4,
    "required": ["#DemoBake"],
    "first": [],
    "last": []
  },
  "research": {"mode": "auto", "lookback_days": 7, "fallback_days": 30},
  "field_map": {
    "素材编号": "content_id",
    "发布语言": "language",
    "成片说明": "content_brief",
    "参考帖子": "reference_url"
  }
}
```

DemoBake 仅为配置演示，不是全局默认品牌。这个示例采用最多 4 个标签，`#DemoBake` 已占一个位置，剩余最多 3 个从与素材相关且有依据的候选中选；不会为了凑满而补通用流量词。

如必须固定首尾，可用 `first: ["#DemoBake"]`、`last: ["#YourCampaign"]`；它们自动成为必选标签。需要严格数量时把 `count_mode` 改为 `exact`。同一标签不会重复出现，互相矛盾的首尾或数量规则会被指出。

配置可省略非必需字段，省略项使用技能默认值。详细字段含义、校验及输入别名见 [数据约定](DATA_CONTRACT.md)。`field_map` 的方向是源列名到内部字段名，不能写反。配置是给 Codex 阅读的，不是一个可独立执行的程序。

## 输入准备

可直接用文字说明，也可使用 `assets/input-template.csv` 的表头；模板只有表头，没有伪装成真实素材的样例行。Excel 无需改成固定模板，只要说明对应列即可。

每条至少明确平台、目标语言和素材事实；批次统一值可写在消息或项目配置中。热点名称、样片链接、已知参考文案、人物、账号定位有则补充。

特别留意：

- 口播文案是声音或制作指导，不自动等于发布 Caption。
- “计划让猫落地”不证明成片已出现落地镜头。
- 原始明星视频不证明二创中的主体就是该明星。
- 旧 Caption 与新素材冲突时，需要说明哪版有效；技能不会把二者混在一起写。
- 用户贴的文案、截图转录和第三方搜索摘要可作为不同强度的线索，但不自动证明当下热度。

## 如何看交付结果

单条默认在对话里给文案、译文、标签、可复制贴文和状态。批量默认在新建的 `post-copy-runs/<唯一运行目录>/` 下提供：

- `post_copy_result.xlsx`：发布结果和处理范围内的原始行数据。
- `post_copy_result.csv`：与结果对应的 UTF-8 BOM 文件。
- `research_evidence.xlsx`：逐标签依据、参考文案类型和访问限制。
- `run_report.md`：处理范围、实际采用的规则、统计和异常。

状态为：

- `SUCCESS`：本次事实、格式和适用的证据检查通过；不是流量保证，也不表示已经发布。
- `NEEDS_REVIEW`：文案可作为草稿，但有用户文字/间接证据、页面受阻或其他待判断问题，需按原因复核。
- `FAILED`：缺少必要资料、核心事实冲突未解，或无法满足明确硬性要求；最终贴文留空，保留可用草稿和原因。

无法核实热度不等于标签一定不相关。证据表会区分“原帖实际可读”“仅搜索线索”“用户提供”“项目指定”和“未验证候选”。未验证候选不会混入最终标签。完整字段及检查项见 [数据约定](DATA_CONTRACT.md)。

## 安装与携带

安装单位是整个 `social-post-copy/` 文件夹，包含 `SKILL.md`、`agents/`、`references/` 和 `assets/`，不要只复制 SKILL.md。放入运行 Codex 的技能目录：通常是 `~/.codex/skills/social-post-copy`；若环境设置了 `CODEX_HOME`，则使用其下的 `skills/social-post-copy`。

同名目录已存在时，先比较内容并保留本地修改，不用本说明里的安装步骤作为覆盖授权。换电脑或交给其他使用者时可携带整个文件夹；新项目只需自己的输入和可选的 `post-copy.project.json`，不需复制旧项目运行目录。

安装后在新项目聊天中使用 `$social-post-copy`。如果当前聊天尚未识别新技能，可新开聊天再调用；也可在消息里提供 SKILL.md 的绝对路径，请 Codex 按该文件执行。

## 适用边界

本技能不替代社交平台发布工具，不自动登录、发布、排期或给他人发送结果。默认不看视频画面或音轨；写作事实需要你提供，或在明确要求分析媒体后另行补充。它也不执行产品研究、口播脚本创作或内容增长策略。

实际写作质量仍需结合账号语气、最终成片和母语习惯审阅。联网参考是否可读、表格能否生成取决于当前运行环境；不把未经真实联机测试的能力宣称为已验证。
