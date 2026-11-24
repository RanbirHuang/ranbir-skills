# vfx-pair-delivery

审核「源视频 → 特效视频」训练数据对，并生成交付包的 Agent Skill（Claude / Codex 通用）。

每个 Pair 输出：`<pair_id>_source.mp4`、`<pair_id>_target.mp4`、`instruction.txt`（英中各一行）、`qa.csv`、`manifest.jsonl`、`sha256.txt`；批次根目录另有 `qa_all.csv`、`manifest_all.jsonl` 和 `report.md` 检查报告。

## 开始使用

```text
请用 $vfx-pair-delivery 审核这 4 条视频并生成交付包。
视频和信息在：<多维表格链接或本地文件夹>
```

或直接运行脚本：

```bash
python3 scripts/package_pairs.py pairs.json --out ./交付包 --config config.json
```

`pairs.json` 字段见 [SKILL.md](SKILL.md)，示例见 `examples/`。依赖：Python 3.9+、ffmpeg/ffprobe、numpy、opencv-python。

## 自动检查要点

- 分辨率低于 1280×720 或源/目标尺寸差异大 → 拒绝；尺寸差 ≤1% 只提示
- 帧率、帧数、时长有小差异（默认 ≤1 秒）→ 只提示，不拒绝
- 码率不足、含音轨、可变帧率、非 16:9 → 提示（可在 config 里改成拒绝）
- 非特效区一致性：MAD ≤2/255、SSIM ≥0.98（试标后校准）
- 指令长度：英文 ≤60 词，中文 ≤60 字

## 安装

将整个 `vfx-pair-delivery/` 目录放到 `~/.codex/skills/vfx-pair-delivery/`（Codex）或 `~/.claude/skills/vfx-pair-delivery/`（Claude Code）。保留 `scripts/`、`examples/`、`agents/`。
