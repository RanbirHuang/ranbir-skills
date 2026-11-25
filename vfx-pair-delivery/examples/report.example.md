# 交付包检查报告

## P1-snow-000001 — reject

- 源：2048×1080 30.0fps 150帧 5.0s h264 11.99Mbps 音轨1
- 目标：1322×696 24.128fps 113帧 4.683s h264 11.99Mbps 音轨1
- 检查：format=fail fps_and_time=warn bitrate=warn aligned=False preserved=False（MAD 7.32，SSIM 0.9345，ROI [0.0, 0.124, 1.0, 1.0]）
- ❌ target 分辨率 1322×696 低于最低 1280×720
- ❌ 源/目标分辨率不一致（2048×1080 vs 1322×696）
- ⚠️ source 含音轨（建议去除）
- ⚠️ target 含音轨（建议去除）
- ⚠️ target 非恒定帧率（VFR）
- ⚠️ 源画幅非 16:9（2048×1080）
- ⚠️ 帧率/帧数/时长有差异但在容差内（30.0fps/150帧/5.0s vs 24.128fps/113帧/4.683s）
- ⚠️ source 码率 11.99Mbps 低于要求 20.0Mbps
- ⚠️ 非特效区差异 MAD 7.32/255、SSIM 0.9345（要求 ≤2.0、≥0.98，试标校准）

## P1-depression-000001 — reject

- 源：2048×1080 30.0fps 191帧 6.367s h264 11.99Mbps 音轨1
- 目标：1322×696 24.094fps 153帧 6.35s h264 11.96Mbps 音轨1
- 检查：format=fail fps_and_time=warn bitrate=warn aligned=False preserved=True（MAD 1.94，SSIM 0.9881，ROI [0.0, 0.604, 1.0, 1.0]）
- ❌ target 分辨率 1322×696 低于最低 1280×720
- ❌ 源/目标分辨率不一致（2048×1080 vs 1322×696）
- ⚠️ source 含音轨（建议去除）
- ⚠️ target 含音轨（建议去除）
- ⚠️ target 非恒定帧率（VFR）
- ⚠️ 源画幅非 16:9（2048×1080）
- ⚠️ 帧率/帧数/时长有差异但在容差内（30.0fps/191帧/6.367s vs 24.094fps/153帧/6.35s）
- ⚠️ source 码率 11.99Mbps 低于要求 20.0Mbps

## P2-fire-000001 — pass

- 源：2050×1080 30.0fps 226帧 7.533s h264 11.99Mbps 音轨1
- 目标：2052×1080 30.0fps 202帧 6.733s h264 11.8Mbps 音轨1
- 检查：format=warn fps_and_time=warn bitrate=warn aligned=False preserved=True（MAD 1.18，SSIM 0.9941，ROI [0.339, 0.0, 0.676, 1.0]）
- ⚠️ source 含音轨（建议去除）
- ⚠️ target 含音轨（建议去除）
- ⚠️ 源/目标分辨率有细微差异（2050×1080 vs 2052×1080），建议导出时对齐
- ⚠️ 源画幅非 16:9（2050×1080）
- ⚠️ 帧率/帧数/时长有差异但在容差内（30.0fps/226帧/7.533s vs 30.0fps/202帧/6.733s）
- ⚠️ source 码率 11.99Mbps 低于要求 20.0Mbps
- ⚠️ target 码率 11.8Mbps 低于要求 20.0Mbps

## P2-halo-000001 — pass

- 源：1920×1080 30.0fps 216帧 7.2s h264 11.99Mbps 音轨1
- 目标：1920×1080 30.0fps 212帧 7.067s h264 11.82Mbps 音轨1
- 检查：format=warn fps_and_time=warn bitrate=warn aligned=False preserved=False（MAD 3.16，SSIM 0.9756，ROI [0.37, 0.0, 0.722, 0.563]）
- ⚠️ source 含音轨（建议去除）
- ⚠️ target 含音轨（建议去除）
- ⚠️ 帧率/帧数/时长有差异但在容差内（30.0fps/216帧/7.2s vs 30.0fps/212帧/7.067s）
- ⚠️ source 码率 11.99Mbps 低于要求 20.0Mbps
- ⚠️ target 码率 11.82Mbps 低于要求 20.0Mbps
- ⚠️ 非特效区差异 MAD 3.16/255、SSIM 0.9756（要求 ≤2.0、≥0.98，试标校准）
