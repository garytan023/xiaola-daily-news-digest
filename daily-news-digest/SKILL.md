---
name: daily-news-digest
description: 每日电商/营销/媒介行业资讯精选从 RSS 抓取到飞书文档的完整流程。当 Gary 要求"每天自动发资讯"、"日报"或需要"昨日资讯精选"时触发。支持手动执行和 cron 自动调度。
---

# daily-news-digest

每日电商/营销/媒介行业资讯精选。抓取 45 个微信公众号 RSS 源 → AI 评分筛选 → 生成飞书文档 → 发送飞书消息通知 Gary。

## 快速执行

```bash
python3 ~/.openclaw/workspace-dev/skills/daily-news-digest/scripts/rss_digest.py
```

执行后输出：
- 本地 Markdown：`~/.openclaw/workspace-dev/output/rss_daily_YYYY-MM-DD.md`
- 飞书文档链接（打印到 stdout）

## 工作流程

1. **抓取** - 并行抓取 45 个 RSS 源（微信公众号 via RSSHub）
2. **去重** - 按标题指纹排重 + 噪音词过滤
3. **日期过滤** - 只保留昨天内容
4. **排他分类** - 每个文章只归一个最相关分类（抖音/小红书/京东/阿里妈妈/电商零售/营销+AI/营销增长）
5. **AI 评分** - 按营销洞察/案例+媒介投放+电商运营+AI营销打分
6. **精选** - 每分类最多 8 条，按分数降序
7. **生成文档** - 写入飞书云文档
8. **通知** - 发飞书 DM 给 Gary，包含文档链接

## 关键文件

- `scripts/rss_digest.py` - 主脚本
- `scripts/rss_digest.py` 中 `OPML_FILE` 指向 `~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml`
- `OUTPUT_FILE` 输出到 `~/.openclaw/workspace-dev/output/rss_daily_YYYY-MM-DD.md`

## Cron 调度（6:30 AM 每日）

```
0 6 * * * python3 ~/.openclaw/workspace-dev/skills/daily-news-digest/scripts/rss_digest.py
```

## 发送通知

脚本最后会打印飞书文档 URL。若需要程序化发送飞书消息，在 cron job 的 `agentTurn` prompt 中让 agent：
1. 运行脚本获取文档 URL
2. 用 `message(action=send, channel=feishu, to=user:ou_d635f4f3d20ac474cf8575038b5d2b33, message=...)` 发送摘要卡片

## 分类说明

排他性分类逻辑（按优先级）：
1. 小红书关键词 → 小红书
2. 京东关键词 → 京东
3. 阿里妈妈关键词 → 阿里妈妈
4. 抖音关键词 → 抖音
5. AI相关关键词 → 营销+AI
6. 电商/零售/直播关键词 → 电商零售
7. 其他 → 营销增长

## 已知限制

- 微信公众号 RSS 不暴露阅读量/在看/评论等互动指标
- 互动数据如有需要，需通过新榜/蝉妈妈/飞瓜数据 API（付费）
