"""
Few-shot prompt for urgency classification.
Classifies overall market risk as low/medium/high/critical.
Outputs structured JSON.
"""

SYSTEM_PROMPT = (
    "You are a financial risk assessment system. "
    "Analyze the provided market data and classify the overall risk level. "
    "Output valid JSON only. No explanations outside the JSON."
)

FEW_SHOT_TEMPLATE = """
Example 1 — LOW RISK:
Input: Stocks up 1-2%, positive sentiment (avg +0.4), VIX at 14, no 8-K filings.
Output: {{"risk_level": "low", "rationale": "Markets stable with positive momentum across all tracked assets.", "summaries": {{"AAPL": "Steady growth on positive analyst upgrades.", "MSFT": "Cloud revenue continues to expand."}}, "key_findings": [{{"finding": "Broad market optimism on tech earnings", "significance": 0.6, "source": "NewsAPI"}}]}}

Example 2 — MEDIUM RISK:
Input: Mixed signals, one ticker down 3%, sentiment split, CPI rising 0.3%.
Output: {{"risk_level": "medium", "rationale": "Mixed signals with one ticker showing weakness. Inflation data trending upward warrants monitoring.", "summaries": {{"AAPL": "Under pressure from supply chain concerns.", "MSFT": "Performing well despite broader uncertainty."}}, "key_findings": [{{"finding": "CPI increase signals potential rate hike", "significance": 0.7, "source": "FRED"}}, {{"finding": "AAPL supply chain disruption", "significance": 0.65, "source": "NewsAPI"}}]}}

Example 3 — HIGH RISK:
Input: Multiple tickers down 4%+, negative sentiment (avg -0.5), VIX above 25, 8-K filing detected.
Output: {{"risk_level": "high", "rationale": "Significant sell-off with elevated volatility. Material event filing requires immediate review.", "summaries": {{"NVDA": "Sharp decline on semiconductor demand fears.", "TSLA": "Under pressure from regulatory scrutiny."}}, "key_findings": [{{"finding": "8-K material event filing for NVDA", "significance": 0.95, "source": "SEC EDGAR"}}, {{"finding": "VIX spike above 25 signals market fear", "significance": 0.85, "source": "yfinance"}}]}}

Example 4 — CRITICAL:
Input: Broad market crash >7%, extreme negative sentiment, VIX above 35, multiple 8-K filings, Fed emergency action.
Output: {{"risk_level": "critical", "rationale": "Systemic risk event. Multiple material filings, extreme volatility, and emergency policy action detected.", "summaries": {{"ALL": "Broad-based selling across all tracked assets."}}, "key_findings": [{{"finding": "Market-wide circuit breaker triggered", "significance": 1.0, "source": "yfinance"}}, {{"finding": "Fed emergency rate action", "significance": 0.98, "source": "FRED"}}]}}
"""


def build_prompt(data_summary: str) -> str:
    """Build the urgency classification prompt with few-shot examples."""
    return f"""{SYSTEM_PROMPT}

{FEW_SHOT_TEMPLATE}

Now analyze this data and output a JSON object with risk_level, rationale, summaries, and key_findings:

{data_summary}

Output (valid JSON only):"""
