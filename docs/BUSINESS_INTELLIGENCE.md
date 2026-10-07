# MultiMind AI — Business Intelligence & KPI Architecture

The Business Intelligence (BI) module computes financial, commercial, and operational metrics directly from tabular data and generates strategic narrative insights.

---

## 1. Core Financial Formulas & Metrics

MultiMind AI implements industry-standard commercial formulas:

### Gross Profit
$$\text{Gross Profit} = \text{Total Revenue} - \text{Total Cost}$$

### Profit Margin Percentage
$$\text{Profit Margin (\%)} = \left(\frac{\text{Gross Profit}}{\text{Total Revenue}}\right) \times 100$$

### Period-Over-Period Sales Growth Rate
$$\text{Growth Rate (\%)} = \left(\frac{\text{Current Period Value} - \text{Previous Period Value}}{\text{Previous Period Value}}\right) \times 100$$

### Average Order Value (AOV)
$$\text{AOV} = \frac{\text{Total Revenue}}{\text{Total Distinct Orders}}$$

---

## 2. Multi-Dimensional Breakdown (`app/business_intelligence/analytics.py`)

* **Product Performance:** Ranks top products by gross revenue, units sold, and contribution percentage.
* **Customer Performance:** Identifies top accounts driving revenue concentration.
* **Category Breakdown:** Aggregates revenue shares across categories.

---

## 3. Automated Insight Generation (`app/business_intelligence/insights.py`)

Synthesizes executive recommendations based on mathematical outcomes:
* **Margin Health:** Flags healthy ($>30\%$), moderate ($10\% - 30\%$), and low-margin ($<10\%$) scenarios.
* **Growth Momentum:** Evaluates period-over-period expansion or contraction.
* **Concentration Risk:** Triggers portfolio diversification warnings if a single product or customer represents over $40\%$ of total revenue.
