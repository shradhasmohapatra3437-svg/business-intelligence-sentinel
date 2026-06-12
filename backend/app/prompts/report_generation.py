"""
Full report generation prompt.
Generates a structured markdown intelligence report with specific sections.
"""

SYSTEM_PROMPT = (
    "You are an expert financial analyst at a major consulting firm. "
    "Write a comprehensive, professional market intelligence report in Markdown. "
    "Be analytical, not speculative. Cite sources for every finding. "
    "Use tables, risk badges, and structured sections."
)


def build_prompt(
    risk_level: str,
    stock_data: dict,
    sentiment_data: dict,
    macro_data: list,
    filings_data: dict,
    key_findings: list,
    aspect_highlights: dict = None,
) -> str:
    """Build the complete report generation prompt."""

    # Format stock summary
    stock_section = "## Stock Data\n"
    for ticker, data in stock_data.items():
        price = data.get("current_price", "N/A")
        change = data.get("daily_change_pct", 0)
        stock_section += f"- **{ticker}**: ${price} (daily change: {change:+.2f}%)\n"

    # Format sentiment summary
    sentiment_section = "## Sentiment Analysis Results\n"
    for ticker, articles in sentiment_data.items():
        if isinstance(articles, list):
            avg_pos = 0
            avg_neg = 0
            count = len(articles)
            for a in articles:
                scores = a.get("finbert_scores", {})
                avg_pos += scores.get("positive", 0)
                avg_neg += scores.get("negative", 0)
            if count > 0:
                avg_pos /= count
                avg_neg /= count
            sentiment_section += (
                f"- **{ticker}**: {count} headlines analyzed, "
                f"avg positive: {avg_pos:.2f}, avg negative: {avg_neg:.2f}\n"
            )

    # Format aspect highlights
    aspect_section = ""
    if aspect_highlights:
        aspect_section = "## Aspect-Level Sentiment Highlights\n"
        for ticker, aspects in aspect_highlights.items():
            if aspects:
                aspect_section += f"### {ticker}\n"
                for aspect, score in aspects.items():
                    emoji = "🟢" if score > 0.3 else ("🔴" if score < -0.3 else "🟡")
                    aspect_section += f"- {emoji} **{aspect}**: {score:+.2f}\n"

    # Format macro indicators
    macro_section = "## Macroeconomic Indicators\n"
    for indicator in macro_data:
        if isinstance(indicator, dict) and not indicator.get("error"):
            name = indicator.get("name", indicator.get("series_id", ""))
            value = indicator.get("current_value")
            change = indicator.get("change_pct")
            if value is not None:
                macro_section += f"- **{name}**: {value}"
                if change is not None:
                    macro_section += f" (change: {change:+.2f}%)"
                macro_section += "\n"

    # Format SEC filings
    filings_section = "## SEC Filings\n"
    has_filings = False
    for ticker, filings in filings_data.items():
        for f in filings:
            if isinstance(f, dict) and not f.get("error"):
                has_filings = True
                form = f.get("form_type", "")
                date = f.get("filed_date", "")
                priority = "🚨 HIGH PRIORITY" if f.get("is_material_event") else ""
                filings_section += f"- **{ticker}** {form} ({date}) {priority}\n"
    if not has_filings:
        filings_section += "- No significant filings in the last 30 days.\n"

    # Format key findings
    findings_section = "## Key Findings\n"
    for finding in key_findings[:5]:
        if isinstance(finding, dict):
            text = finding.get("finding", "")
            sig = finding.get("significance", 0)
            source = finding.get("source", "")
            findings_section += f"- **{text}** (significance: {sig:.2f}, source: {source})\n"

    return f"""{SYSTEM_PROMPT}

Generate a comprehensive intelligence report based on the following data.
Overall risk level: **{risk_level.upper()}**

{stock_section}

{sentiment_section}

{aspect_section}

{macro_section}

{filings_section}

{findings_section}

Write the report with these exact sections:
1. **Executive Summary** — 2-3 sentence overview with risk level badge
2. **Market Overview** — Price table with daily changes
3. **Key Findings** — Top 3-5 findings with risk badges and significance scores
4. **Aspect Sentiment Breakdown** — Table per ticker showing DeBERTa ABSA results
5. **Economic Indicators** — Current values and trend direction
6. **SEC Filing Alerts** — Any material events (8-K gets 🚨 badge)
7. **Recommended Actions** — Concrete next steps based on data
8. **Methodology & Sources** — List all data sources used

Use markdown tables, emoji risk badges (🟢🟡🔴🚨), and professional tone.
Output the full markdown report:"""
