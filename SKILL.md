---
name: bean-scan
description: 监控 @BroBean88（Bean哥）Twitter 推文，自动采集→邮件推送→小红书发布→飞书通知。Bean哥中文推文无需翻译。依赖 Camofox 浏览器 + Hermes cron。
version: 1.0.0
author: hermes
tags: [monitoring, twitter, bean, brobean, camofox, cron, social, xiaohongshu, email]
dependencies:
  - camofox-browser
  - xhs-note-creator
---

# Bean Scan — Bean哥推文监控

监控 @BroBean88（Bean哥）的 Twitter 推文，全自动流水线：

```
Camofox 浏览器采集推文 → 去重（snowflake ID）→ 
  → 🥇 邮件群发（67人BCC）
  → 🥈 小红书卡片发布（原文卡片 + 可选的解读正文）
  → 🥉 飞书推送
```

**与 Serenity Scan 的区别：**
- Bean哥推文是**中文**，无需翻译
- 卡片主题可定制（默认 Tiffany 蓝）
- 每 33 分钟采集一次（与 Serenity 错峰，避免 Camofox 争抢）

## 前置依赖

### 1. Camofox 浏览器
```bash
hermes skills install camofox-browser
curl http://localhost:9377/health  # → {"ok":true}
```

### 2. 小红书发布
```bash
hermes skills install xhs-note-creator
cd /opt/data/skills/xhs-note-creator
cat > .env << 'EOF'
XHS_COOKIE="a1=...; web_session=...;"
EOF
```

### 3. 邮件脚本（可选）
将 `scripts/send_serenity_emails.py` 复制到 `/opt/data/scripts/`，修改 `RECIPIENTS` 列表。

## 快速开始

### Step 1: 部署监控脚本
```bash
cp scripts/monitor_brobean.py /opt/data/scripts/
chmod +x /opt/data/scripts/monitor_brobean.py

# 首次运行（静默播种）
python3 /opt/data/scripts/monitor_brobean.py
```

### Step 2: 创建 cron 任务
```bash
# Schedule: every 33m（与 Serenity every 1m 错峰）
# Script: monitor_brobean.py
# Skills: bean-scan（本技能）
# Deliver: feishu
# Enabled toolsets: terminal, file
```

## 工作流详解

### 监控脚本 (monitor_brobean.py)

1. 通过 Camofox API 打开 `https://x.com/BroBean88`
2. 等待 SPA 加载 → 滚动 → 两遍 "Show more" 展开
3. JS 提取前 5 条推文（作者过滤：`/BroBean88/status/`，注意大小写！）
4. 全文补全：每条约 8s，从独立推文页提取完整文本
5. Snowflake ID 去重 + 输出 JSON

**⚠️ 大小写陷阱**：`String.includes()` 区分大小写。`/Brobean88/` ≠ `/BroBean88/`。必须用精确的大小写匹配 X 页面上实际的状态链接。

### Agent 处理（cron prompt）

**🥇 STEP 1: 邮件推送** — 同上（send_serenity_emails.py）

**🥈 STEP 2: 小红书发布**
- Bean哥推文是中文 → **无需翻译**，原文即内容
- 卡片可用 `xhs_tweet_card.py` 或 `brobean_card.py`（Tiffany 蓝主题）

**🥉 STEP 3: 飞书推送** — 同上

## Cron Prompt 模板

```
Read the data-collection script output below. It contains JSON: {"count": N, "tweets": [...], "checked_at": "..."}.

If "count" == 0 OR there is no output → respond with exactly "[SILENT]" and nothing else.

If "count" > 0 → process ALL tweets. EXECUTION ORDER IS MANDATORY:

━━━━━━━━━━━━━━━━━━━━━━
🥇 STEP 1: 邮箱推送（MUST BE FIRST）
━━━━━━━━━━━━━━━━━━━━━━
cat > /tmp/email_body.txt << 'EMAILEOF'
发文时间（北京时间）：[UTC+8]
原文：> [tweet original - Chinese]
解读：[short Chinese analysis, WeChat style]
链接：[tweet URL]
EMAILEOF
python3 /opt/data/scripts/send_serenity_emails.py "🔔 Bean哥 新推文" /tmp/email_body.txt --tweet-id <TWEET_ID>

━━━━━━━━━━━━━━━━━━━━━━
🥈 STEP 2: 小红书卡片发布（可选）
━━━━━━━━━━━━━━━━━━━━━━
# Bean哥推文中文，无需翻译
DIR=$(mktemp -d)
python3 /opt/data/scripts/xhs_tweet_card.py \
  --tweet "原文" --time "UTC时间" \
  --translation "原文" --out "$DIR"
cd /opt/data/skills/xhs-note-creator && python3 scripts/publish_xhs.py \
  --title "Bean哥推文" --desc "解读正文" \
  --images $(ls "$DIR"/card_*.png | sort) --public
rm -rf "$DIR"

━━━━━━━━━━━━━━━━━━━━━━
🥉 STEP 3: Feishu 推送
━━━━━━━━━━━━━━━━━━━━━━
**发文时间（北京时间）：** [UTC+8]
**原文：** > [original]
**解读：** [analysis]
**链接：** [tweet URL]
```

## 与 Serenity Scan 共存

两个监控脚本共享 Camofox（同一端口 9377），必须错峰运行：

| 任务 | 周期 | 说明 |
|------|------|------|
| Serenity scan | every 1m | 高频，全天候 |
| Bean scan | every 33m | 低频，使用质数间隔避免与 Serenity 重叠 |

**如果同时运行导致 Camofox 超时，增大间隔或错开启动时间。**

## 缓存与去重

- `.brobean_cache/last_max_id.txt` — snowflake ID 缓存
- `.brobean_cache/.seeded` — 首次播种标记
- 与 Serenity 缓存完全隔离（不同目录）

## 故障排查

| 症状 | 原因 | 修复 |
|------|------|------|
| 脚本始终输出 0 | 大小写错误 | 检查 `/BroBean88/`（两个大 B）|
| 推文截断 | "Show more" 未完全展开 | 确认两遍 expand_js + full-text fallback |
| Camofox 争抢 | 与 Serenity 同时运行 | 增大间隔到 37m 或其他质数 |

## 目录结构

```
bean-scan/
├── SKILL.md                    # 本文件
├── scripts/
│   ├── monitor_brobean.py      # 推文采集脚本
│   └── send_serenity_emails.py # 邮件群发脚本（67人BCC）
└── references/
    └── cron-prompt-full.md     # 完整 cron prompt
```
