#!/usr/bin/env python3
"""
RSS 精选脚本 v4
- 排他性分类（每篇文章只归一个分类，不重复）
- 带原文链接
- 提取正文中的互动指标（阅读量/在看/评论等显式数据）
- 只输出昨天内容
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import re, html, os

OPML_FILE = os.path.expanduser('~/.openclaw/workspace-dev/data/wechat_rss_subscriptions.opml')
TIMEOUT = 12
CST = timezone(timedelta(hours=8))
YESTERDAY = datetime.now(CST) - timedelta(days=1)
YD_STR = YESTERDAY.strftime('%Y-%m-%d')
YD_SHORT = YESTERDAY.strftime('%m-%d')
OUTPUT_FILE = os.path.expanduser(f'~/.openclaw/workspace-dev/output/rss_daily_{YD_STR}.md')
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
ATOM_NS = 'http://www.w3.org/2005/Atom'
CONTENT_NS = 'http://purl.org/rss/1.0/modules/content/'

CAT_EMOJI = {
    '京东': '🟣', '字节': '🔵', '小红书': '🔴', '腾讯': '🟢', '百度': '⚪',
    '营销+AI': '🤖', '电商零售': '🛒', '营销增长': '📈'
}
# 平台分类只接收官方账号；第三方账号全部进入 topic 分类
CAT_ORDER = ['京东', '字节', '小红书', '腾讯', '百度', '营销+AI', '电商零售', '营销增长']

# 来源账号 → 平台官方分类（优先级最高）
SOURCE_PLATFORM_MAP = {
    # 京东
    "京东黑板报": "京东",
    "京准通": "京东",
    "京麦商家中心": "京东",
    "京东研究院": "京东",
    # 字节/抖音
    "巨量引擎营销观察": "字节",
    "巨量引擎营销科学": "字节",
    "抖音电商营销观察": "字节",
    # 小红书
    "小红书种草学": "小红书",
    "小红书商业动态": "小红书",
    "小红书技术REDtech": "小红书",
    # 腾讯
    "腾讯广告": "腾讯",
    # 百度
    "百度营销观": "百度",
}

def tag(local):
    return f'{{{ATOM_NS}}}{local}'

def parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        dt = datetime.strptime(text[:25], '%a, %d %b %Y %H:%M:%S')
        return dt.replace(tzinfo=timezone.utc).astimezone(CST)
    except:
        try:
            dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
            return dt.astimezone(CST)
        except:
            return None

def classify(title, content, source):
    """排他性分类：
    - 官方平台账号（SOURCE_PLATFORM_MAP） → 对应平台分类
    - 其他账号 → 按内容关键词分入 topic 分类（京东/字节/小红书/百度只接收官方账号）
    """
    # 官方平台账号优先 → 进入平台分类
    if source in SOURCE_PLATFORM_MAP:
        return SOURCE_PLATFORM_MAP[source]
    # 第三方账号 → 只能进入 topic 分类
    t = (title or '').lower()
    c = ((content or '')[:3000]).lower()
    # topic 关键词（排他）
    if any(k in t or k in c for k in ['ai', '人工智能', 'gpt', '大模型', '自动化', 'aigc', '数字人',
                                          'deepseek', 'chatgpt', '智能投放', 'geo', 'ai营销', 'claude',
                                          'genai', 'llm', 'agent', '智能体', '工作流', 'gpt-4', 'o1', 'o3', 'gemini']):
        return '营销+AI'
    if any(k in t or k in c for k in ['电商', '零售', '直播带货', '天猫', '淘宝', '选品', '跨境',
                                          '亚马逊', 'shopify', '私域', '拼多多', '唯品会', '即时零售',
                                          '货架电商', '跨境电商', '电商平台', '电商运营', '京东', 'jd.com']):
        return '电商零售'
    return '营销增长'

def score_article(title, content):
    t = (title or '').lower()
    c = ((content or '')[:3000]).lower()
    score = 0
    case_kw = ['案例', '实战', '方法论', '数据', 'gmv', 'roi', '转化率', '投放效果',
                '销售额', '增长', '操盘', '策略', '复盘', '分析报告', '洞察', '拆解',
                '全链路', '种草', '收割', '同比增长', '突破', '暴跌', '首破', '新高',
                '周报', '周刊', '月报', '季报', '年报', '榜单', '趋势', '报告']
    score += min(3, sum(1 for k in case_kw if k in t or k in c))
    media_kw = ['投放', '广告', '信息流', '关键词', '出价', '预算', '竞价', 'cpm', 'cpc',
                'ocpm', '达播', '品牌自播', '投放策略', '代理商', '媒介', '广告主']
    score += min(2, sum(1 for k in media_kw if k in t or k in c))
    ec_kw = ['电商', '零售', '选品', '供应链', '直播带货', '天猫', '淘宝', '跨境',
             '亚马逊', 'shopify', '私域', '复购', '客单价', '电商平台', '拼多多',
             '京东', '外卖', '即时零售', '货架电商']
    score += min(2, sum(1 for k in ec_kw if k in t or k in c))
    ai_kw = ['ai', '人工智能', 'gpt', '大模型', '自动化', 'aigc', '数字人',
              '智能投放', 'geo', 'ai营销', 'deepseek', 'claude', 'chatgpt',
              'genai', 'llm', 'agent', '智能体', '工作流']
    score += min(2, sum(1 for k in ai_kw if k in t or k in c))
    if len(content or '') > 500 and '。' in c:
        score += 1
    # 噪音惩罚
    noise_kw = ['被抓', '被调查', '震惊', '热招', '招聘', '亿级卖家交流会', '峰会', '论坛',
                 '沙龙', '活动报名', '扫码抢位', '席位紧张', '免费领取', '限时报名',
                 '转发', '收藏', '点在看', '阅读原文']
    score -= sum(2 for k in noise_kw if k in t)
    # 低质指标惩罚
    if any(k in t for k in ['马斯克', '特朗普', '普京', '拜登', '关税']):
        score -= 1
    if title and len(title) < 12:
        score -= 1
    return max(0, score)

def is_noise(title):
    t = (title or '')
    noise = ['招聘', '诚聘', '猎头', '免费领', '限时抢', '立即购买', '优惠码',
             '满减', '0元', '转给朋友', '扩散', '建议收藏', '朋友圈', '求职']
    return any(k in t for k in noise)

def normalize_text(text):
    if not text:
        return ''
    t = text.strip().lower()
    for ch in '【】[]（）()｜|:：,,。.!！？?""\'\'、、/-_':
        t = t.replace(ch, ' ')
    return ' '.join(t.split())

def title_fp(title):
    tokens = [tok for tok in normalize_text(title).split() if len(tok) > 1]
    return ' '.join(tokens[:12])

def parse_feed(feed_url, feed_title):
    try:
        r = requests.get(feed_url, timeout=TIMEOUT)
        r.encoding = 'utf-8'
        root = ET.fromstring(r.text)
        items = []
        for entry in root.findall('.//' + tag('entry')):
            title_el = entry.find(tag('title'))
            link_el = entry.find(tag('link'))
            updated_el = entry.find(tag('updated'))
            content_el = entry.find(f'{{{CONTENT_NS}}}encoded')
            title = html.unescape(title_el.text or '') if title_el is not None else ''
            link = (link_el.get('href') or '') if link_el is not None else ''
            pub = parse_date(updated_el.text if updated_el is not None else '')
            content = html.unescape(content_el.text) if content_el is not None and content_el.text else ''
            if not title or not link:
                continue
            items.append({'title': title, 'link': link, 'pub': pub, 'source': feed_title, 'content': content})
        return items
    except:
        return []

def extract_plain_text(html_content):
    if not html_content:
        return ''
    try:
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:3000]
    except:
        return ''

def extract_engagement(text):
    """从正文中提取显式的互动指标"""
    result = {}
    if not text:
        return result
    t = text[:6000]
    # 阅读量：优先找"阅读10万+"、"阅读量：100万+"等格式
    m = re.search(r'阅读[量数：:]*\\s*([\\d十百千万余\\.]+万\\+?)', t)
    if m:
        result['阅读量'] = m.group(1)
    m = re.search(r'([\\d\\.]+万\\+?)\\+?\\s*(?:阅读|浏览)', t)
    if m and '阅读量' not in result:
        result['阅读量'] = m.group(1)
    # 在看/点赞
    m = re.search(r'在看[：:]*\\s*([\\d十百千万余\\.]+万\\+?)', t)
    if m:
        result['在看'] = m.group(1)
    # 评论
    m = re.search(r'评论[数：:]*\\s*([\\d十百千万余\\.]+万\\+?)', t)
    if m:
        result['评论'] = m.group(1)
    m = re.search(r'([\\d\\.]+万\\+?)\\s*(?:评论|留言)', t)
    if m and '评论' not in result:
        result['评论'] = m.group(1)
    # 转发
    m = re.search(r'转发[量：:]*\\s*([\\d十百千万余\\.]+万\\+?)', t)
    if m:
        result['转发'] = m.group(1)
    return result

def first_sentence(text, max_len=120):
    """提取第一句有意义的正文"""
    if not text:
        return ''
    # 跳过开头常见噪音（导航、版权、摘要等）
    skip_prefixes = ['来源', '作者', '未经授权', '转载', 'copyright', '©', '相关阅读',
                     '点击', '关注', '扫描', '二维码', '免责声明', '广告', '推广']
    sentences = re.findall(r'[^。！？.!?]{20,150}[。！？.!?]', text)
    for s in sentences:
        lower_s = s.lower()
        if not any(s.lower().startswith(p.lower()) for p in skip_prefixes):
            return s[:max_len]
    return (text[:max_len] + '…') if len(text) > max_len else text

# === 主流程 ===
print("Step 1: 解析 OPML...")
tree = ET.parse(OPML_FILE)
feeds = [(o.get('xmlUrl'), o.get('title', '')) for o in tree.getroot().findall('.//outline[@xmlUrl]')]
print(f"  共 {len(feeds)} 个 RSS 源")

print("Step 2: 并行抓取 feeds...")
all_items = []
seen_fp = set()

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(parse_feed, url, title): (url, title) for url, title in feeds}
    for i, future in enumerate(as_completed(futures)):
        try:
            for item in future.result():
                fp = title_fp(item['title'])
                if fp and fp not in seen_fp and not is_noise(item['title']):
                    seen_fp.add(fp)
                    all_items.append(item)
        except:
            pass
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(feeds)}")

print(f"  去重后: {len(all_items)} 条")

# 只保留昨天
yd_start = datetime(YESTERDAY.year, YESTERDAY.month, YESTERDAY.day, 0, 0, 0, tzinfo=CST)
yd_end = datetime(YESTERDAY.year, YESTERDAY.month, YESTERDAY.day, 23, 59, 59, tzinfo=CST)
recent = [it for it in all_items if it['pub'] and yd_start <= it['pub'] <= yd_end]
print(f"  昨天 {YD_SHORT}: {len(recent)} 条")

# 排他性分类 + 打分 + 正文提取 + 互动指标
seen_links = set()  # 额外去重：同链接只保留一条
for it in recent:
    plain = extract_plain_text(it['content'])
    it['text'] = plain
    it['score'] = score_article(it['title'], plain)
    it['cat'] = classify(it['title'], plain, it['source'])
    it['engagement'] = extract_engagement(plain)

# 再次去重（排他性分类后，同链接不重复）
deduped = []
for it in recent:
    if it['link'] not in seen_links:
        seen_links.add(it['link'])
        deduped.append(it)

recent = deduped
print(f"  排他分类+去重后: {len(recent)} 条")

# 按分类分组，分类内按分数降序，每分类最多8条
by_cat = defaultdict(list)
for it in recent:
    by_cat[it['cat']].append(it)
for cat in by_cat:
    by_cat[cat].sort(key=lambda x: x['score'], reverse=True)

print("\n各分类条数：")
for cat in CAT_ORDER:
    if cat not in by_cat:
        continue
    items = by_cat[cat]
    top = items[0]['score'] if items else 0
    print(f"  {cat}: {len(items)} 条 (最高分: {top})")

# 生成 Markdown
lines = [
    f'# 每日资讯精选 | {YD_STR}（昨日）\n',
    f"\n> 共抓取 **{len(all_items)}** 条 \\| 昨日去重 **{len(all_items)}** 条 \\| 排他分类 **{len(recent)}** 条\n",
    "> 评分：营销洞察/案例(0-3) + 媒介投放(0-2) + 电商运营(0-2) + AI营销(0-2) + 内容质量(0-1)\n",
    "> 注：微信 RSS 不暴露阅读量等指标；若有数据均为文章正文中显式提及\n",
    "\n---\n",
]

MIN_SCORE = 4  # 低于此分的文章不进入精选
AD_KEYWORDS = ['金冠俱乐部', '独角招聘', '热招中', '晋升通道', '员工福利', '招聘岗位']  # 明显广告帖直接过滤
MAX_TOTAL = 40  # 精选总条数上限

# 收集所有精选，再全局截断
all_qualified = []
for cat in CAT_ORDER:
    if cat not in by_cat or not by_cat[cat]:
        continue
    qualified = [
        it for it in by_cat[cat]
        if it['score'] >= MIN_SCORE
        and not any(k in (it['title'] or '') for k in AD_KEYWORDS)
    ]
    all_qualified.extend([(it, cat) for it in qualified])

# 按分数降序，截断至 MAX_TOTAL
all_qualified.sort(key=lambda x: x[0]['score'], reverse=True)
capped = all_qualified[:MAX_TOTAL]

# 按 CAT_ORDER 分组输出
for cat in CAT_ORDER:
    items = [it for it, c in capped if c == cat]
    if not items:
        continue
    emoji = CAT_EMOJI.get(cat, '📝')
    lines.append(f"\n## {emoji} {cat}（{len(items)}条）\n")
    for it in items:
        pub_str = it['pub'].strftime('%m-%d %H:%M') if it['pub'] else ''
        eng = it['engagement']
        eng_str = ''
        if eng:
            parts = [f"{k}：{v}" for k, v in eng.items()]
            eng_str = ' | ' + ' '.join(parts)
        lines.append(f"### [{it['title']}]({it['link']})")
        lines.append(f"\n来源：{it['source']} \| {pub_str} \| 评分：**{it['score']}/10**{eng_str}\n")
        sent = first_sentence(it['text'])
        if sent:
            lines.append(f"\n> {sent}\n")
        lines.append("\n---\n")

output = '\n'.join(lines)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(output)

size = os.path.getsize(OUTPUT_FILE)
qualified_total = len(capped)
print(f"\n完成！\n文件: {OUTPUT_FILE}\n大小: {size} bytes")
print(f"总条数: {len(recent)}条 | 精选(≥{MIN_SCORE}分): {qualified_total}条")

