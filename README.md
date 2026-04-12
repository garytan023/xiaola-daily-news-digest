# 📰 daily-news-digest

每日电商/营销/媒介行业资讯精选 Skill for OpenClaw。

## 功能

- 抓取 **45 个微信公众号 RSS 源**（通过 RSSHub）
- AI 评分筛选（营销洞察/案例、媒介投放、电商运营、AI营销）
- 排他性分类：抖音 / 小红书 / 京东 / 阿里妈妈 / 电商零售 / 营销+AI / 营销增长
- 生成飞书云文档
- 每天 6:30 AM 自动发飞书 DM 给 Gary

## 安装

```bash
# 下载 .skill 文件后安装
/clawhug install daily-news-digest.skill

# 或克隆仓库后安装
git clone https://github.com/garytan023/xiaola-daily-news-digest.git
/clawhug install xiaola-daily-news-digest/daily-news-digest.skill
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `daily-news-digest.skill` | 可直接安装的 Skill 包 |
| `daily-news-digest/SKILL.md` | Skill 说明文档 |
| `daily-news-digest/scripts/rss_digest.py` | 主脚本 |

## RSS 订阅源

45 个微信公众账号，覆盖：Morketing、36氪、虎嗅、亿邦动力、天下网商、SocialBeta、艾瑞咨询、巨量引擎营销观察、京东研究院、腾讯广告等。

## 定时任务

Cron: `30 6 * * *` (Asia/Shanghai)

## 已知限制

- 微信公众号 RSS 不暴露阅读量/在看/评论等互动指标
- 互动数据如有需要，需通过新榜/蝉妈妈/飞瓜数据 API（付费）

## 作者

小拉（拉小风）for Gary Tan
