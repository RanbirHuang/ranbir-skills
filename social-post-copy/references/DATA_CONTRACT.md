# 输入、证据与交付约定

## 输入映射

`field_map` 的方向是“源文件列名 → 内部字段名”。同一内部字段若映射到多个非空且冲突的值，应指出冲突，不能覆盖丢失信息。优先使用显式映射，其次识别下列常见含义；陌生字段先看内容，不靠名字相近强行映射。

- `content_id`：内容 ID、视频编号、视频 ID。用户 ID 重复时保留原值，另用“工作表 + 原行号”作为唯一关联键，不能覆盖记录。
- `platform`：发布平台；允许从可识别的帖子链接推断。多平台须展开为独立记录，保留同一源行。
- `market`：目标市场、国家或地区。不是语言代码。
- `language`：目标语言、Post语言。明确输入优先于批次默认；“英文”等可归一为 `en`，但不暗自推定英美地区。
- `topic_id` / `topic_description`：热点组 ID / 热点描述、内容主题。没有热点也可执行。
- `content_brief`：素材要求、素材内容简述、成片文字描述。
- `reference_url`：参考帖子、样片链接、热点链接。多个链接保留原值并分别记录。产品页、制作模板链接是背景资料，不自动作为社交帖子证据。
- `reference_caption`：用户提供的参考 Caption 或已发布原文。旧计划里的待发布文案不自动是正确事实或已发布证据。
- `account_positioning`：账号定位；`featured_people`：本条明确出现的人物。

平台、语言、素材事实可来自单行、已确认的批次说明或项目配置。不同主题、平台、市场和语言的研究不可无条件串用。`口播文案`、制作提示词、镜头要求不自动映射为发布 Caption，也不自动证明成片已实现相关动作。

读取 Excel 时保留公式，不改写源文件；公式缓存缺失不能当空素材静默丢行。保留 `source_file`、`source_sheet`、真实 `source_row`、用户 ID 和唯一 `record_key`。不要默认只处理第一张表；相关工作表、隐藏行和筛选范围有歧义时先判断用户范围，再询问确有影响的部分。

## 配置的实际含义

配置模板见 `assets/project-profile.example.json`。该配置由 Codex 解释执行，不是带有自动校验器的程序接口。未识别字段、错误类型、负数或互相冲突的配置应指出，不要悄悄忽略。

- 字符串空值表示未提供，不是“请生成一个品牌/语言”。语言缺失且无法从已确认说明补齐时，该条无法完成。
- `translation_language` 默认 `zh-CN`；设为 `null` 表示不生成翻译。其他明确语言也可使用，对应字段仍为 `caption_translation`，不要误标中文。
- `emoji.min/max` 是每条范围，需为非负整数且 min 不大于 max。翻译保留原 Caption 所用 Emoji。`allow_mentions=false` 时 Caption 不含 `@` 账号。
- `max_caption_chars=null` 表示未配置项目上限。若有整数上限，按 Unicode 码点计数，包含空格和 Emoji，仅计 Caption；如用户要求平台特定算法或完整贴文长度，单独说明并按要求检查。此配置不代表平台当前官方限制。
- `hashtags.count_mode` 为 `at_most` 或 `exact`，`count` 为非负整数。默认最多 5 个；`count=0` 且无指定标签可不输出标签。`exact` 数量不足时失败，不凑数。
- `hashtags.first`、`required`、`last` 是标签数组，含 `#`。first 和 last 自身也是必选词；required 中未出现在首尾的标签可放中间。合并后每个标签只出现一次，首尾按各自顺序排列，动态标签填充中间。首尾要求同一标签同时占不同位置等无法满足的规则应先指出；所有必选词去重后的数量大于 count 时配置冲突，停止受影响记录。去重时至少忽略 `#` 差异和拉丁字母大小写，输出保留指定或原帖拼写。
- `research.mode=auto`：按任务需要研究；`required`：必须尝试外部查证，失败后标明原因并降级为需复核；`off`：只使用用户资料，不访问外部来源、不声称已验证当下热度。如果用户本轮明确要求实时查证，以其要求为准。
- `lookback_days=7`、`fallback_days=30` 是查找近期参考的默认窗口，需为正整数且 fallback 不小于 lookback。窗口不足时可以找背景，但不得把旧数据标为近期证据。观察日期不等于帖子发布日期，两者分别记录。

## 证据记录

每个选定标签都要有记录；指定词也记录 `project_required` 及规则出处。没有网页的用户证据可不填 URL，填写具体文件、工作表、行号或用户消息出处。不能用占位链接代替真实来源。

每条证据至少保留：

- `evidence_id`、`record_key`、`topic_id`、`tag`、`category`（品牌/主题/人物/内容等）。
- `evidence_grade`：`observed_post`、`search_evidence`、`user_supplied`、`project_required`、`unverified`。
- `source_url` 或 `source_location`、`observed_at`（含时区）、`published_at`（可为空）。
- `source_excerpt`：实际可见的短摘录或忠实要点；`relevance_note`：为什么支持本条标签；`verification_note`：可见范围与限制。
- `metric_name`、`metric_value`、`metric_observed_at`：仅在实际可核实时填写，不把缺失值写为零，不从播放量推断点赞量。

候选标签可在证据表保留 `unverified`，但必须标明 `selected=false`，不计入最终标签数量。没有证据记录不是某标签不存在的证明。

文案参考另保留 `reference_type`：`exact_topic`（同热点/主题）、`creator_style`（仅创作者风格）、`source_context`（原片/背景）、`unavailable`（原帖不可读）。每条有链接、可见文案要点、验证说明；不可读时文案留空，不据搜索摘要还原原文。共享研究通过 evidence_id 关联到每条使用记录。

## 默认批量交付

在当前项目下创建新的 `post-copy-runs/<时间戳或唯一ID>/`，已有目录不覆盖。用户指定输出位置时以其要求为准；不把结果写进全局技能安装目录。每次运行保留实际采用的规则摘要及覆盖说明，便于同一配置下复查。

`post_copy_result.xlsx`：

- `Results`：发布字段优先显示，至少有 `record_key`、内容 ID、平台、市场、语言、Caption、翻译、Hashtag、完整贴文、写作形式、状态、复核原因及源表行定位。
- `Source rows`：所处理范围内的原始列值、源文件/工作表/行号及 record_key。保留数据可追溯性，不要求复刻原表样式。

`post_copy_result.csv`：UTF-8 BOM，每条与 Results 对齐，机器字段为 `record_key, content_id, platform, market, language, caption, caption_translation, hashtags, post_text, caption_style, status, review_reason, source_file, source_sheet, source_row`。无翻译时 translation 留空；hashtags 为以空格连接的单行文本。

`research_evidence.xlsx`：`Hashtag evidence` 与 `Caption references` 两个工作表。没有外部研究也保留用户资料/项目规则依据，并明确标注外部研究未进行或不可用。

`run_report.md`：输入与处理范围、实际规则、记录/分组数、三种状态计数、证据来源概况、校验结果、逐条异常及未完成项。多平台拆行时同时报告源行数和输出记录数，避免把扩展数量算成遗漏或重复。运行未完成时如实报告，不伪称所有记录已处理。

`post_text` 拼接规则：有标签时为 `caption + "\n\n" + hashtags`；无标签时只保留 Caption。`FAILED` 的 post_text 必须为空，可用草稿仍留在 caption/translation 字段；`NEEDS_REVIEW` 可有完整贴文，但状态与原因必须可见。复核说明不混入可复制的贴文正文。

导出后重新打开并核对：源行到输出记录关联、各状态计数、精确数量或最大数量、指定词排序、实际拼接结果、中文/日文/韩文等字符、缺失值、重复 ID。用户文本以文本保存，防止 CSV/Excel 将以 `=` 等开头的文案当公式执行；导出转义应保持可见原文，并核对回读结果。未完成的语义审阅、翻译自然度或联网查证要单独说明。
