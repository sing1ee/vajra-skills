---
name: company-value-analysis
description: >
  公司价值深度分析。用户给出公司名称或股票代码，自动搜索并生成"懂了一个公司"的系统检验报告。
  覆盖商业模式、护城河、财务指标、管理层、估值五个层次。
  触发词：分析公司、公司价值分析、company analysis、analyze company、研究一下XX公司、XX值不值得买。
user_invocable: true
---

# 公司价值深度分析 (Company Value Analysis)

综合段永平、邱国鹭、特里·史密斯、格林布拉特等投资框架，对一家公司进行系统性"五层检验"分析。

## 使用方法

```bash
/company-value-analysis AAPL
/company-value-analysis 腾讯
/company-value-analysis 600519
```

用户提供公司名称或股票代码，技能自动完成数据收集与分析报告生成。

---

## 执行流程

### Step 0: 确认标的

根据用户输入，确认公司名称和对应的股票代码（可能有多个上市地）。如果用户给的是中文公司名，先搜索确认对应的 ticker symbol。

- A 股代码格式：`600519.SS`（上交所）、`000858.SZ`（深交所）
- 港股代码格式：`0700.HK`
- 美股代码格式：`AAPL`、`MSFT`

### Step 1: 获取核心财务数据 (yfinance)

使用 uvx 运行 yfinance 获取公司基本面数据：

```bash
cat > /tmp/company_fundamentals.py << 'PYEOF'
import yfinance as yf
import json

TICKER = "__TICKER__"

t = yf.Ticker(TICKER)

# 基本信息
info = t.info
basic = {
    "公司名称": info.get("longName") or info.get("shortName", "N/A"),
    "行业": info.get("industry", "N/A"),
    "板块": info.get("sector", "N/A"),
    "国家": info.get("country", "N/A"),
    "员工数": info.get("fullTimeEmployees", "N/A"),
    "简介": info.get("longBusinessSummary", "N/A")[:500],
    "市值": info.get("marketCap", "N/A"),
    "企业价值EV": info.get("enterpriseValue", "N/A"),
}

# 盈利能力指标
profitability = {
    "毛利率": info.get("grossMargins", "N/A"),
    "营业利润率": info.get("operatingMargins", "N/A"),
    "净利润率": info.get("profitMargins", "N/A"),
    "ROE": info.get("returnOnEquity", "N/A"),
    "ROA": info.get("returnOnAssets", "N/A"),
}

# 估值指标
valuation = {
    "PE_TTM": info.get("trailingPE", "N/A"),
    "PE_Forward": info.get("forwardPE", "N/A"),
    "PB": info.get("priceToBook", "N/A"),
    "PS": info.get("priceToSalesTrailing12Months", "N/A"),
    "EV/EBITDA": info.get("enterpriseToEbitda", "N/A"),
    "EV/Revenue": info.get("enterpriseToRevenue", "N/A"),
    "PEG": info.get("pegRatio", "N/A"),
}

# 成长指标
growth = {
    "营收增长率": info.get("revenueGrowth", "N/A"),
    "盈利增长率": info.get("earningsGrowth", "N/A"),
    "季度营收增长YoY": info.get("revenueQuarterlyGrowth", "N/A"),
    "季度盈利增长YoY": info.get("earningsQuarterlyGrowth", "N/A"),
}

# 现金流与分红
cashflow = {
    "经营现金流": info.get("operatingCashflow", "N/A"),
    "自由现金流": info.get("freeCashflow", "N/A"),
    "总现金": info.get("totalCash", "N/A"),
    "总债务": info.get("totalDebt", "N/A"),
    "股息率": info.get("dividendYield", "N/A"),
    "派息比率": info.get("payoutRatio", "N/A"),
}

# 股价信息
price = {
    "当前价格": info.get("currentPrice") or info.get("regularMarketPrice", "N/A"),
    "52周最高": info.get("fiftyTwoWeekHigh", "N/A"),
    "52周最低": info.get("fiftyTwoWeekLow", "N/A"),
    "50日均线": info.get("fiftyDayAverage", "N/A"),
    "200日均线": info.get("twoHundredDayAverage", "N/A"),
    "Beta": info.get("beta", "N/A"),
}

result = {
    "基本信息": basic,
    "盈利能力": profitability,
    "估值指标": valuation,
    "成长指标": growth,
    "现金流与分红": cashflow,
    "股价信息": price,
}

print(json.dumps(result, ensure_ascii=False, indent=2))
PYEOF
uvx --from yfinance --with pandas python3 /tmp/company_fundamentals.py
```

将 `__TICKER__` 替换为实际的 ticker symbol。

### Step 2: 获取历史财务报表 (yfinance)

获取近 4 年的关键财务数据，用于分析趋势：

```bash
cat > /tmp/company_financials.py << 'PYEOF'
import yfinance as yf
import json
import pandas as pd

TICKER = "__TICKER__"

t = yf.Ticker(TICKER)

def df_to_dict(df):
    """将 DataFrame 转为可读 dict，处理 NaN 和 Timestamp"""
    if df is None or df.empty:
        return {}
    result = {}
    for col in df.columns:
        col_key = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        result[col_key] = {}
        for idx in df.index:
            val = df.loc[idx, col]
            if pd.isna(val):
                result[col_key][str(idx)] = None
            elif isinstance(val, (int, float)):
                result[col_key][str(idx)] = round(float(val), 2)
            else:
                result[col_key][str(idx)] = str(val)
    return result

# 利润表（年度）
income = df_to_dict(t.financials)
# 资产负债表（年度）
balance = df_to_dict(t.balance_sheet)
# 现金流量表（年度）
cashflow = df_to_dict(t.cashflow)

# 计算关键衍生指标
def calc_derived(financials_df, balance_df, cashflow_df):
    derived = {}
    try:
        fin = t.financials
        bal = t.balance_sheet
        cf = t.cashflow
        if fin is None or bal is None:
            return derived

        for col in fin.columns[:4]:  # 最近4年
            year = col.strftime("%Y") if hasattr(col, "strftime") else str(col)
            d = {}

            # ROIC = NOPAT / Invested Capital
            ebit = fin.loc["EBIT", col] if "EBIT" in fin.index else None
            tax = fin.loc["Tax Provision", col] if "Tax Provision" in fin.index else None
            net_income = fin.loc["Net Income", col] if "Net Income" in fin.index else None
            total_assets = bal.loc["Total Assets", col] if "Total Assets" in bal.index and col in bal.columns else None
            current_liab = bal.loc["Current Liabilities", col] if "Current Liabilities" in bal.index and col in bal.columns else None
            total_equity = bal.loc["Stockholders Equity", col] if "Stockholders Equity" in bal.index and col in bal.columns else None
            total_debt_val = bal.loc["Total Debt", col] if "Total Debt" in bal.index and col in bal.columns else None
            total_revenue = fin.loc["Total Revenue", col] if "Total Revenue" in fin.index else None

            if ebit and tax and net_income and ebit != 0:
                tax_rate = abs(float(tax)) / abs(float(ebit)) if ebit != 0 else 0.25
                nopat = float(ebit) * (1 - tax_rate)
                if total_equity and total_debt_val:
                    invested_capital = float(total_equity) + float(total_debt_val)
                    if invested_capital != 0:
                        d["ROIC"] = round(nopat / invested_capital * 100, 2)

            # ROE
            if net_income and total_equity and float(total_equity) != 0:
                d["ROE"] = round(float(net_income) / float(total_equity) * 100, 2)

            # 资产负债率
            if total_assets and total_equity and float(total_assets) != 0:
                total_liab = float(total_assets) - float(total_equity)
                d["资产负债率"] = round(total_liab / float(total_assets) * 100, 2)

            # 自由现金流 / 净利润
            if cf is not None and col in cf.columns:
                fcf = cf.loc["Free Cash Flow", col] if "Free Cash Flow" in cf.index else None
                if fcf and net_income and float(net_income) != 0:
                    d["FCF/净利润"] = round(float(fcf) / float(net_income) * 100, 2)

            derived[year] = d
    except Exception as e:
        derived["error"] = str(e)
    return derived

derived = calc_derived(t.financials, t.balance_sheet, t.cashflow)

# 只输出关键行项目，避免数据过多
key_income_items = [
    "Total Revenue", "Gross Profit", "EBIT", "EBITDA",
    "Net Income", "Basic EPS", "Diluted EPS"
]
key_balance_items = [
    "Total Assets", "Total Liabilities Net Minority Interest",
    "Stockholders Equity", "Total Debt", "Cash And Cash Equivalents",
    "Current Assets", "Current Liabilities"
]
key_cashflow_items = [
    "Operating Cash Flow", "Capital Expenditure", "Free Cash Flow",
    "Repurchase Of Capital Stock", "Cash Dividends Paid"
]

def filter_items(data, keys):
    filtered = {}
    for period, items in data.items():
        filtered[period] = {k: v for k, v in items.items() if k in keys}
    return filtered

output = {
    "利润表(关键项)": filter_items(income, key_income_items),
    "资产负债表(关键项)": filter_items(balance, key_balance_items),
    "现金流量表(关键项)": filter_items(cashflow, key_cashflow_items),
    "衍生指标(ROIC/ROE等)": derived,
}

print(json.dumps(output, ensure_ascii=False, indent=2))
PYEOF
uvx --from yfinance --with pandas python3 /tmp/company_financials.py
```

### Step 3: 获取机构持仓与分析师评级 (yfinance)

```bash
cat > /tmp/company_analysts.py << 'PYEOF'
import yfinance as yf
import json
import pandas as pd

TICKER = "__TICKER__"

t = yf.Ticker(TICKER)

result = {}

# 分析师推荐
try:
    rec = t.recommendations
    if rec is not None and not rec.empty:
        recent = rec.tail(10)
        result["分析师推荐(近期)"] = recent.to_dict(orient="records")
except:
    pass

# 分析师目标价
try:
    info = t.info
    result["分析师目标价"] = {
        "最高目标价": info.get("targetHighPrice", "N/A"),
        "最低目标价": info.get("targetLowPrice", "N/A"),
        "平均目标价": info.get("targetMeanPrice", "N/A"),
        "中位目标价": info.get("targetMedianPrice", "N/A"),
        "当前价格": info.get("currentPrice") or info.get("regularMarketPrice", "N/A"),
        "推荐评级": info.get("recommendationKey", "N/A"),
        "推荐人数": info.get("numberOfAnalystOpinions", "N/A"),
    }
except:
    pass

# 主要持仓机构
try:
    holders = t.institutional_holders
    if holders is not None and not holders.empty:
        holders_list = holders.head(10).to_dict(orient="records")
        # 处理 Timestamp
        for h in holders_list:
            for k, v in h.items():
                if hasattr(v, "strftime"):
                    h[k] = v.strftime("%Y-%m-%d")
                elif pd.isna(v):
                    h[k] = None
        result["前10大机构持仓"] = holders_list
except:
    pass

# 内部人交易
try:
    insider = t.insider_transactions
    if insider is not None and not insider.empty:
        insider_list = insider.head(10).to_dict(orient="records")
        for item in insider_list:
            for k, v in item.items():
                if hasattr(v, "strftime"):
                    item[k] = v.strftime("%Y-%m-%d")
                elif pd.isna(v):
                    item[k] = None
        result["内部人交易(近期)"] = insider_list
except:
    pass

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
PYEOF
uvx --from yfinance --with pandas python3 /tmp/company_analysts.py
```

### Step 4: 搜索定性信息 (Web Search)

这一步是关键差异化步骤。需要通过网络搜索获取以下定性信息，每个主题独立搜索：

**必须搜索的主题（至少执行以下 6 次搜索）：**

1. **商业模式与竞争格局**
   - 搜索词：`"[公司名] business model competitive advantage moat"`
   - 目的：理解公司怎么赚钱、差异化来源

2. **行业竞争格局与市场份额**
   - 搜索词：`"[行业] market share competitive landscape 2025 2026"`
   - 目的：判断"月亮还是星星"，竞争格局是寡头还是百舸争流

3. **管理层与公司文化**
   - 搜索词：`"[公司名] CEO management culture capital allocation"`
   - 目的：评估管理层是"造钟人"还是"报时人"

4. **风险因素与争议**
   - 搜索词：`"[公司名] risks challenges controversy 2025 2026"`
   - 目的：发现潜在的价值陷阱或成长陷阱信号

5. **近期重大事件与战略方向**
   - 搜索词：`"[公司名] latest news strategy 2025 2026"`
   - 目的：了解最新动态、战略调整

6. **同行估值对比**
   - 搜索词：`"[公司名] vs [竞争对手] valuation comparison PE"`
   - 目的：横向对比估值水平

**搜索工具优先级：**
- 优先使用 `mcp__web-search-prime__web_search_prime` 或 `mcp__MiniMax__web_search`
- 备选使用 tavily-search skill
- 对于关键搜索结果页面，可用 `mcp__web-reader__webReader` 提取全文

**搜索语言策略：**
- 中国公司：同时用中文和英文搜索，中文搜索更多本土视角，英文搜索更多国际视角
- 其他公司：以英文为主

### Step 5: 生成分析报告

综合以上所有数据，生成以下格式的 Markdown 报告：

---

## 报告模板

```markdown
# [公司名称] ([股票代码]) 价值分析报告

> 分析日期：YYYY-MM-DD

## 一句话概括

> [用一句话说清这家公司怎么赚钱。说不清就是没懂。]

---

## 第一层：这是个什么生意？

### 商业模式
- **收入来源**：[主要营收构成，各业务占比]
- **成本结构**：[主要成本项]
- **盈利模式**：[高利润型 / 高周转型 / 高杠杆型 — 杜邦三问]

### 差异化与可复制性
- **差异化来源**：[品牌/技术/网络效应/其他]
- **可复制性**：[能否不断"开店"式扩张]

---

## 第二层：这个生意好不好？

### 波特五力扫描

| 维度 | 评估 | 说明 |
|------|------|------|
| 上游议价权 | 强/中/弱 | ... |
| 下游议价权 | 强/中/弱 | ... |
| 竞争对手 | ... | ... |
| 进入门槛 | 高/中/低 | ... |
| 替代品威胁 | 高/中/低 | ... |

### 竞争格局（邱国鹭"数月亮"）

**格局判断**：月朗星稀 / 一超多强 / 两分天下 / 三足鼎立 / 百舸争流

| 公司 | 市场份额 | 说明 |
|------|----------|------|
| ... | ...% | ... |

### 护城河

| 护城河类型 | 有/无 | 强度 | 说明 |
|-----------|-------|------|------|
| 品牌 | | | |
| 专利/技术 | | | |
| 网络效应 | | | |
| 转换成本 | | | |
| 规模经济 | | | |
| 牌照/准入 | | | |

---

## 第三层：赚钱能力强不强？

### 核心指标（近 4 年趋势）

| 指标 | FY1 | FY2 | FY3 | FY4(最新) | 判断 |
|------|-----|-----|-----|-----------|------|
| 营收(亿) | | | | | |
| 净利润(亿) | | | | | |
| 毛利率 | | | | | |
| 净利率 | | | | | |
| ROE | | | | | 门槛>15% |
| ROIC | | | | | 门槛>15% |
| 自由现金流(亿) | | | | | |
| FCF/净利润 | | | | | 越接近100%越好 |
| 资产负债率 | | | | | |

### Fundsmith 四标准检验

| 标准 | 是否通过 | 说明 |
|------|---------|------|
| 高 ROCE | ✅/❌ | |
| 利润转现金 | ✅/❌ | |
| 高利润率 | ✅/❌ | |
| 穿越周期 | ✅/❌ | |

### 陷阱检查

- [ ] 利润增长但现金流不增长？（应收账款堆积）
- [ ] ROE 高但靠高杠杆？（杜邦拆解）
- [ ] 增长快但不赚钱？（无利润增长陷阱）

---

## 第四层：人和文化靠不靠谱？

### 管理层评估

| 维度 | 评分 | 说明 |
|------|------|------|
| "造钟人" vs "报时人" | | |
| "��润之上"的追求 | | |
| 资本配置能力 | | |
| 诚信与透明度 | | |

### 资本配置分析

近年利润分配方式：
- 再投资占比：...%
- 分红占比：...%
- 回购占比：...%
- 并购占比：...%

**检验：愿不愿意把钱交给这个管理团队 10 年不管？** [回答]

---

## 第五层：现在价格合不合理？

### 估值概览

| 指标 | 当前值 | 行业中位 | 自身5年中位 | 判断 |
|------|--------|---------|------------|------|
| PE (TTM) | | | | |
| PE (Forward) | | | | |
| PB | | | | |
| PS | | | | |
| EV/EBITDA | | | | |
| PEG | | | | |
| 股息率 | | | | |

### 分析师评级

| 项目 | 数值 |
|------|------|
| 推荐评级 | |
| 平均目标价 | |
| 当前价格 | |
| 隐含涨跌幅 | |
| 分析师人数 | |

### 安全边际模式判断

属于哪种安全边际模式？
- [ ] 高ROE + 低PE
- [ ] 龙头地位 + 高股息率
- [ ] 低成本 + 低PE
- [ ] 净现金接近市值
- [ ] 暂无明显安全边际

---

## 快速检查表

| # | 检查项 | 结论 |
|---|--------|------|
| 1 | 能一句话说清它怎么赚钱 | ✅/❌ |
| 2 | 有差异化/定价权，不是纯拼价格 | ✅/❌ |
| 3 | 竞争格局好（寡头/龙头），不是百舸争流 | ✅/❌ |
| 4 | ROIC > 15%，且能持续 | ✅/❌ |
| 5 | 利润能变成真金白银（FCF ≈ 净利润） | ✅/❌ |
| 6 | 管理层靠谱，有长期主义文化 | ✅/❌ |
| 7 | 估值合理，有安全边际 | ✅/❌ |
| 8 | 10年后这公司大概率还在 | ✅/❌ |

**总评**：前6个打了 X/6 个勾。

- 前6个打不了勾 = 没懂，不应该买
- 第7个决定什么时候买
- 第8个决定能不能长拿

---

## 风险提示

### 价值陷阱检查（邱国鹭五类）

| 陷阱类型 | 风险 | 说明 |
|---------|------|------|
| 被技术进步淘汰 | 高/中/低 | |
| 赢家通吃行业里的小公司 | 高/中/低 | |
| 分散的重资产夕阳行业 | 高/中/低 | |
| 景气顶点的周期股 | 高/中/低 | |
| 会计欺诈 | 高/中/低 | |

### 成长陷阱检查（邱国鹭十类）

| 陷阱类型 | 风险 | 说明 |
|---------|------|------|
| 估值过高 | 高/中/低 | |
| 技术路径踏空 | 高/中/低 | |
| 无利润增长 | 高/中/低 | |
| 成长性破产 | 高/中/低 | |
| 盲目多元化 | 高/中/低 | |
| 树大招风 | 高/中/低 | |
| 新产品风险 | 高/中/低 | |
| 寄生式增长 | 高/中/低 | |
| 强弩之末 | 高/中/低 | |
| 会计造假 | 高/中/低 | |

---

## 综合结论

### 一句话判断
> [这家公司值不值得深入研究？为什么？]

### 关键亮点（Bull Case）
1. ...
2. ...
3. ...

### 关键风险（Bear Case）
1. ...
2. ...
3. ...

### 下一步建议
- [如果看好] 建议关注的买入价位区间
- [如果不确定] 建议进一步研究的方向
- [如果看空] 建议回避的原因

---
*数据来源: Yahoo Finance via yfinance, Web Search | 仅供参考，不构成投资建议*
*分析框架: 段永平(right business/people/price) + 邱国鹭(数月亮/杜邦三问) + Fundsmith + Greenblatt*
```

## 分析原则

1. **数据驱动**：所有判断必须基于实际获取的数据和搜索结果，不要编造
2. **定量+定性**：财务数据是骨架，商业洞察是灵魂，两者缺一不可
3. **交叉验证**：多个来源相互印证，避免单一指标误导
4. **诚实标注**：对不确定的地方坦诚标注"信息不足，需进一步研究"
5. **陷阱意识**：始终用价值陷阱和成长陷阱清单审视，避免落入常见坑
6. **客观中立**：呈现事实和逻辑推演，不做过度主观预测
7. **中文输出**：报告以中文撰写，专业术语附英文原文
