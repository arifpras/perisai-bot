# PerisAI: Institutional-Grade Bond Analytics Platform
## Investment Opportunity Overview

---

## Executive Summary

**PerisAI** is a conversational AI platform that brings institutional-grade bond and auction analytics to emerging market traders, portfolio managers, and policy analysts—with zero learning curve.

- **Current Users**: Indonesian government debt traders, fund managers, central bank analysts
- **Technology**: Dual AI personas (Kei: quantitative rigor, Kin: macro narrative) + ML forecasting
- **Data Assets**: 2,000+ bond time series, real-time auction demand forecasts, macro integration
- **Revenue Model**: B2B SaaS subscriptions, API licensing, institutional partnerships

---

## Market Problem

### The Information Asymmetry Gap

**Current State of EM Bond Markets:**
- Indonesian government bonds (SBN) trade $50B+ daily, but information is fragmented
- Traders use spreadsheets + Bloomberg terminals ($25K/year) for basic analysis
- Central banks and regulators lack real-time, interpretable market intelligence
- Local traders and SME fund managers are locked out of institutional-grade tools

**Pain Points:**
1. **Slow research turnaround**: Manually building bond comparison tables takes 30 min–2 hours
2. **Limited analytics depth**: Most traders can't run structural break tests, cointegration analysis, or return attribution
3. **Context gap**: Quantitative models (ARIMA, GARCH) exist but lack market narrative
4. **Forecast opacity**: Demand forecasts are black boxes; no interpretability
5. **Regional exclusivity**: Premium analytics confined to global banks; EM markets underserved

---

## PerisAI Solution: What We've Built

### Core Platform Capabilities

#### 1. **Multi-Asset Bond Analytics** (Real-time)
- **Historical Data**: Indonesian SBN yields/prices (2015–2025, 9 tenors)
- **Live Tables**: Economist-style statistical summaries (Count, Min, Max, Avg, Std)
- **Multi-Tenor Comparisons**: "Show 5Y vs 10Y yield movements Q1 2023 → Q4 2024"
- **Date Flexibility**: Supports month/quarter/year ranges with auto-expansion

**Use Case**: Portfolio manager rebalances in 2 minutes instead of 30.

---

#### 2. **Advanced Time-Series Analytics** (7+ Methods)
Ready-to-run without coding:
- **ARIMA Forecasting**: Automatic 7-model ensemble (ARIMA, ETS, Prophet, VAR, MA, Random Walk, Monte Carlo)
- **GARCH Volatility**: Conditional heteroskedasticity modeling for risk management
- **Cointegration**: Test if yields/FX/VIX move together (pairs trading signals)
- **Granger Causality**: Does inflation lead bond yields? (Hypothesis testing)
- **Rolling Regression**: Track evolving relationships over 90–250-day windows
- **Event Study**: Measure bond response to rate decisions (window analysis)
- **Structural Breaks**: Chow test to detect regime changes (Sept 2024 break detected ✓)

**Use Case**: Quantitative analyst runs 10 analyses in lunch break; publishes research same day.

---

#### 3. **Auction Demand Forecasting** (ML Ensemble, 2026)
- **ML Model**: 4-model ensemble (Random Forest, Gradient Boosting, AdaBoost, Stepwise Regression)
- **Input Features**: 6 macro + auction-specific (deposits, inflation, MOVE index, seasonality)
- **Accuracy**: ~75–80% for 1-month forward, ~70–75% for 2–3 months
- **Output**: Monthly incoming bid forecasts through 2026 with confidence bands

**Use Case**: Debt managers plan 2026 issuance with AI-backed demand projections. Saves BI/MOF millions in foregone issuance.

---

#### 4. **Dual AI Personas** (Interpretability + Narrative)

**Kei (Quantitative Partner)**
- MIT-trained data scientist persona
- Returns: Strict tables, statistical rigor, no speculation
- Handles: All technical analytics, model diagnostics, precise numbers
- Output: HTML tables with raw data, standard deviations, confidence intervals

**Kin (Macro Storyteller)**
- CFA + PhD economist persona
- Returns: Context, headline narratives, geopolitical implications
- Handles: Web search (Perplexity), cross-market relationships, "what does this mean?"
- Output: Prose interpretation, market signals, forward-looking insights

**`/both` Mode**: Chain both—Kei's rigor + Kin's narrative in one output.

**Use Case**: Treasury manager presents analysis to cabinet; explains both numbers AND implications.

---

#### 5. **Natural Language Interface** (Zero Learning Curve)
Users ask in plain English (or Indonesian):
```
/kei auction demand from jan 2026 to dec 2026
→ Table + statistical breakdown + forecast

/both compare yield 5 and 10 year q1 2024 vs q4 2024
→ Kei table + Kin's macro story

/kei garch 5 year p=1 q=1 in 2025
→ Volatility clustering + risk metrics

/check yield 10 year 2025-09-08
→ Structural break detected (Chow p=0.0405)
```

No SQL, Python, or Excel skills required.

---

#### 6. **Real-Time Market Integration**
- **Bond Data**: Daily SBN prices/yields from PDV (live feed)
- **Macro Overlay**: IDR/USD FX rates, VIX index, BI rate  
- **Auction Database**: Consolidated 2010–2026 (historical + 2026 ML forecast)
- **Business Day Awareness**: Auto-skips weekends, Indonesian holidays

---

## Business Opportunities

### Target Markets & Revenue Streams

#### 1. **B2B SaaS: Institutional Subscriptions**
- **Target**: Indonesian fund managers, pension funds, insurance companies
- **Price**: $500–2000/month per institution (vs $25K/year for Bloomberg)
- **Differentiation**: Specialized EM bond + auction focus; dual-persona analysis
- **TAM**: 200+ asset managers in Indonesia × $1000 avg = $200K/month ($2.4M/year)

#### 2. **Government/Central Bank Licensing**
- **Target**: BI (Bank Indonesia), MOF (Ministry of Finance), regional development banks
- **Use Case**: 
  - BI: Real-time auction demand monitoring (manage issuance)
  - MOF: Fiscal planning (demand forecast → debt strategy)
  - Regional Banks: Asset-liability management (spread analysis)
- **Model**: Annual enterprise license ($100K–500K)
- **TAM**: 5–10 institutions × $250K avg = $1.25M–2.5M/year

#### 3. **API & Data Products**
- **Time-Series API**: Fund managers embed PerisAI analytics in their systems
- **Auction Forecast API**: Brokers integrate demand predictions into trading models
- **Data Export**: Historical bond returns, structured auction data, macro indicators
- **Price**: $2K–5K/month per API consumer
- **TAM**: 50+ API users × $3K avg = $150K/month ($1.8M/year)

#### 4. **Research & Advisory Services**
- **Custom Models**: Build bespoke forecasts for specific treasuries or corporate bonds
- **Market Reports**: Weekly/monthly bond market analysis (Kei + Kin deep dives)
- **Training**: Teach portfolio teams how to use advanced analytics
- **Price**: $10K–50K per engagement
- **TAM**: 2–3 engagements/month × $25K avg = $600K–900K/year

#### 5. **Emerging Market Expansion**
- **Adapt for**: Philippines (SB), Thailand (TBD), Vietnam (OGB), India (G-Sec)
- **Model**: Replicate PerisAI architecture to other EM bond markets
- **Revenue**: Same SaaS + licensing model, scaled across 5 countries
- **TAM**: $10M–20M global EM bonds SaaS market

---

## Competitive Advantages

| Feature | PerisAI | Bloomberg Terminal | Local Excel Traders |
|---------|---------|-------------------|-------------------|
| **Cost** | $500–2000/mo | $25K/year | Free (but slow) |
| **Ease of Use** | Natural language | Complex menus | Manual work |
| **EM Bond Focus** | Specialized | Generic | N/A |
| **Auction Forecasting** | ML ensemble, 2026 | Not available | Guesswork |
| **Interpretability** | Dual personas | Black box | Transparent but limited |
| **Time to Insight** | 10 sec query | 5–10 min navigation | 30 min–2 hours |
| **Macro Integration** | FX + VIX overlay | Available | Tedious |
| **Advanced Analytics** | ARIMA, GARCH, Coint, Events | Limited/paid modules | Not feasible |

---

## Technical Moat

### IP & Data Assets
1. **Trained ML Models**: 
   - 2026 auction demand ensemble (proprietary features)
   - Bond return attribution models (carry/duration/roll-down decomposition)
   - Structural break detection (tuned for EM volatility patterns)

2. **Curated Datasets**:
   - 15+ years of Indonesian bond data (clean, deduplicated)
   - Unified auction database (2010–2026)
   - Macro indicators (IDs, sourced & validated)

3. **Proprietary Analytics Code**:
   - ~9000 lines of Telegram bot logic (proven, battle-tested)
   - Custom formatters (Economist-style tables, HTML rendering)
   - Business-day calendar with Indonesian holidays

### Technology Stack
- **Backend**: Python (FastAPI) + PostgreSQL + Telegram/Web APIs
- **ML**: Scikit-learn, Statsmodels, Keras (Prophet)
- **Deployment**: Render (scalable), Docker containerization
- **Frontend**: Web dashboard + Telegram (widespread adoption, no app store friction)

### Scalability Ready
- ✅ API-first architecture (easy to white-label, integrate)
- ✅ Multi-currency support (ready for regional expansion)
- ✅ Modular analytics (can add new time-series methods rapidly)
- ✅ Data pipeline automated (daily feed from PDV, BI, MOF sources)

---

## Financial Projections (3-Year Plan)

### Year 1 (2026)
- **Revenue**: $500K (early SaaS adopters + 1 licensing deal)
- **Costs**: $300K (2 engineers, 1 data scientist, ops)
- **Gross Margin**: 40%

### Year 2 (2027)
- **Revenue**: $2.5M (50 SaaS users, 3 govt licenses, API traction)
- **Costs**: $800K (scale team)
- **Gross Margin**: 68%

### Year 3 (2028)
- **Revenue**: $8M (200+ SaaS, EM expansion pilot, advisory services)
- **Costs**: $2M (regional hires, data ops)
- **Gross Margin**: 75%

---

## Problem-Solving Impact

### 1. **For Treasury Managers (Debt Issuers)**
- **Problem**: Auction demand is unpredictable; issuance planning is guesswork
- **Solution**: ML forecast + market analysis → data-driven debt strategy
- **Impact**: Save $10M–50M in foregone issuance costs; hit optimal pricing windows

### 2. **For Fund Managers (Institutional Investors)**
- **Problem**: Bond research is time-consuming; miss micro-signals (structural breaks, cointegration shifts)
- **Solution**: 2-minute analysis instead of 2-hour Excel grind
- **Impact**: Faster rebalancing, better risk-adjusted returns, lower research costs

### 3. **For Central Banks (Policymakers)**
- **Problem**: Lack real-time market sentiment on debt sustainability
- **Solution**: Daily demand forecast + retail/wholesale bid split
- **Impact**: Better monetary/fiscal coordination, early warning for debt crises

### 4. **For Brokers (Market Makers)**
- **Problem**: Auction bid-ask spreads are wide (low liquidity information)
- **Solution**: Forecast demand → tighter spreads → better client pricing
- **Impact**: Improved market microstructure, lower transaction costs for retail

### 5. **For Regulators (Watchdogs)**
- **Problem**: Can't monitor systemic risk in real-time across bond + FX + equity
- **Solution**: Integrated dashboard with PerisAI analytics + macro links
- **Impact**: Faster detection of market stress, better macroprudential policy

---

## Go-to-Market Strategy

### Phase 1 (Q1–Q2 2026): Proof of Concept
- **Target**: 5–10 early adopter fund managers
- **Approach**: Free pilot with one institution (NDA), showcase results
- **Deliverable**: Case study showing time/cost savings
- **Investment**: $50K (engineering, setup)

### Phase 2 (Q3–Q4 2026): Paid Traction
- **Target**: 20–30 paying SaaS customers + 2 government deals
- **Approach**: Direct sales to portfolio managers, API partnerships with brokers
- **Deliverable**: Scalable onboarding, billing platform
- **Investment**: $200K (sales, product)

### Phase 3 (2027): Regional Expansion
- **Target**: Philippines, Thailand pilots
- **Approach**: Partner with local exchanges, adapt to local data
- **Deliverable**: Multi-country dashboard
- **Investment**: $500K (data ops, regionalization)

---

## Funding Requirements

**Series A: $2.5M** to accelerate to $2.5M+ ARR by 2027

### Use of Funds:
- **Engineering (50%)**: 3 full-stack engineers + 1 data scientist ($1.25M)
- **Sales & Marketing (20%)**: Regional business development, case studies ($500K)
- **Data Ops (20%)**: Real-time data pipelines, API infrastructure ($500K)
- **Legal & Admin (10%)**: IP protection, regulatory compliance ($250K)

---

## Exit Scenarios

1. **Acquisition by Bloomberg / Refinitiv**: $50M–150M (EM analytics bolt-on)
2. **Trade Sale to Indonesian Exchanges**: $20M–40M (strategic integration)
3. **PE Growth Investment**: $10M–30M (path to $30M+ ARR by 2030)
4. **Public Markets**: IPO path if regional EM analytics platforms scale

---

## Team & Advisors

### Founding Team
- **Arif (CEO)**: Data science, Python/ML, EM bond market deep expertise
- **Engineering**: Full-stack developers, API architecture
- **Data Science**: ML model development, time-series forecasting

### Advisor Network (Needed)
- Former BI official (market credibility, regulatory pathway)
- Senior fund manager (UX feedback, enterprise sales)
- Blockchain/fintech entrepreneur (scaling playbook)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| **Forecast accuracy declines** | Ensemble approach reduces model risk; continuous retraining |
| **Competition from Bloomberg** | Niche focus (EM bonds), lower cost, superior UX |
| **Data sourcing breaks** | Direct integrations with PDV, BI, MOF; redundant feeds |
| **Regulatory changes** | Early engagement with BI/MOF; compliance-first design |
| **Market adoption slow** | Pilot with 1–2 anchor institutions; word-of-mouth among traders |

---

## Why Now?

1. **EM Bond Boom**: Indonesian debt market growing $100B+ annually; institutional investor influx
2. **AI Maturity**: LLMs (Kei) + ML forecasting (2026) now practical, cost-effective
3. **Regulatory Tailwind**: BI pushing financial data transparency; appetite for market intelligence
4. **Regional Precedent**: Fintech adoption in Indonesia (GCash, OVO) shows tech appetite
5. **Data Availability**: Clean, structured bond/auction data now accessible (PDV standardization)

---

## One-Pager Summary

| Metric | Value |
|--------|-------|
| **Market Size (EM bonds SaaS)** | $10M–50M globally |
| **TAM (Indonesia only)** | $2.4M–3.5M/year |
| **Current Revenue** | $0 (pre-commercial) |
| **Unit Economics** | 75%+ gross margin; 6-month payback |
| **Time to $1M ARR** | 12–18 months (conservative) |
| **Competitive Moat** | ML models + curated data + UX |
| **Key Risk** | Adoption velocity in regulated environments |
| **Upside Case** | $20M+ ARR by 2030 (regional expansion) |

---

## Contact & Next Steps

**Interested in a demo?**
- Live platform walkthrough (5 min)
- Technical deep-dive (20 min)
- Business model Q&A (15 min)

**Let's talk.** We're raising to turn EM bond traders into data-driven decision-makers.

---

*PerisAI v.0493 | Institutional-grade bond analytics for emerging markets*
