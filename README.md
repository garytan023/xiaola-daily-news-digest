# 📰 daily-news-digest

每日电商/营销/媒介行业资讯精选 Skill for OpenClaw。

## 功能

- 抓取 **45 个微信公众号 RSS 源**（通过 RSSHub）
- AI 评分筛选（营销洞察/案例、媒介投放、电商运营、AI营销、内容质量）
- **排他性分类**：
  - 平台分类（仅官方账号）：京东 / 字节 / 小红书 / 腾讯 / 百度
  - Topic 分类（所有第三方账号）：营销+AI / 电商零售 / 营销增长
- **广告帖自动过滤**：金冠俱乐部、独角招聘、热招中、晋升通道等关键词自动排除
- **精选上限 40 条**，评分门槛 MIN_SCORE=4
- 生成飞书云文档（链接内嵌每条新闻）
- 每天 6:30 AM 自动发飞书 DM

## 分类规则

```
官方平台账号 → 对应平台分类（京东/字节/小红书/腾讯/百度）
                若官方账号当天未发布 → 该分类留空
第三方账号   → 按内容关键词分入 Topic 分类
                营销洞察/案例/AI相关 → 营销+AI
                电商/零售/平台运营   → 电商零售
                增长/趋势/战略      → 营销增长
```

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

## 安装

```bash
# 下载 .skill 文件后安装
clawhug install daily-news-digest.skill

# 或克隆仓库后安装
git clone https://github.com/garytan023/xiaola-daily-news-digest.git
clawhug install xiaola-daily-news-digest/daily-news-digest.skill
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
