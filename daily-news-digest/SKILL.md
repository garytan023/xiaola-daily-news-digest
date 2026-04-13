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
- 精选条数统计（stdout）

## 工作流程

1. **抓取** - 并行抓取 45 个 RSS 源（微信公众号 via RSSHub）
2. **去重** - 按标题指纹排重 + 噪音词过滤
3. **日期过滤** - 只保留昨天内容
4. **排他分类** - 官方平台账号入平台分类；第三方账号按内容关键词入 Topic 分类
5. **广告过滤** - 自动排除含"金冠俱乐部/独角招聘/热招中"等关键词的帖子
6. **AI 评分** - 按营销洞察/案例(0-3) + 媒介投放(0-2) + 电商运营(0-2) + AI营销(0-2) + 内容质量(0-1)
7. **精选** - MIN_SCORE=4 分；全球精选上限 40 条
8. **生成文档** - 写入飞书云文档（链接内嵌每条新闻标题）
9. **通知** - 发飞书 DM 给 Gary

## 分类体系

### 平台分类（仅官方账号）

| 分类 | 来源示例 |
|------|---------|
| 京东 | 京东广告/京东黑板报/京东研究院 |
| 字节 | 抖音官方/巨量引擎/千川 |
| 小红书 | 小红书商业化/REDtech |
| 腾讯 | 腾讯广告/微信派 |
| 百度 | 百度营销 |

> 若官方账号当天未发布，该分类留空。

### Topic 分类（所有第三方账号）

| 分类 | 触发关键词 |
|------|-----------|
| 营销+AI | AI/人工智能/大模型/DeepSeek/Agent/智能体 |
| 电商零售 | 电商/零售/天猫/淘宝/亚马逊/拼多多/即时零售 |
| 营销增长 | 其他营销/品牌/增长/趋势相关内容 |

## 评分标准

| 维度 | 分值 |
|------|------|
| 营销洞察/案例 | 0-3 |
| 媒介投放 | 0-2 |
| 电商运营 | 0-2 |
| AI营销 | 0-2 |
| 内容质量 | 0-1 |
| **总分** | **0-10** |

精选门槛：≥4分；精选上限：40条

## 关键文件

- `scripts/rss_digest.py` - 主脚本
- `OPML_FILE` → `~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml`
- `OUTPUT_FILE` → `~/.openclaw/workspace-dev/output/rss_daily_YYYY-MM-DD.md`

## Cron 调度

- 时间：`30 6 * * *` (Asia/Shanghai, 6:30 AM)
- 建议 sessionTarget: current（避免 isolated session 网络超时）

## 已知限制

- 微信公众号 RSS 不暴露阅读量/在看/评论等互动指标
- 互动数据如有需要，需通过新榜/蝉妈妈/飞瓜数据 API（付费）
