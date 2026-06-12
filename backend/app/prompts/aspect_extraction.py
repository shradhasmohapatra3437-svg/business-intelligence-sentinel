"""
Few-shot prompt for extracting financial entities from headlines.
Used by Gemma 3B (Ollama) or Groq in the ABSA pipeline Step 2a.
"""


SYSTEM_PROMPT = (
    "You are a financial entity extraction system. "
    "Extract the key financial entities, concepts, and aspects from news headlines. "
    "Return ONLY a comma-separated list of 2-4 entities. No explanations."
)

FEW_SHOT_EXAMPLES = [
    {
        "headline": "Tesla cuts prices amid demand concerns",
        "entities": "Tesla, pricing strategy, consumer demand",
    },
    {
        "headline": "Fed raises rates, bank stocks fall",
        "entities": "Federal Reserve, interest rates, bank stocks",
    },
    {
        "headline": "Apple iPhone sales surge but supply chain risks remain",
        "entities": "iPhone sales, supply chain, Apple revenue",
    },
    {
        "headline": "NVIDIA earnings beat expectations as AI chip demand soars",
        "entities": "NVIDIA earnings, AI chips, semiconductor demand",
    },
    {
        "headline": "Goldman Sachs announces layoffs amid cost-cutting push",
        "entities": "Goldman Sachs, workforce reduction, operating costs",
    },
]


def build_prompt(headline: str) -> str:
    """Build the complete few-shot prompt for aspect extraction."""
    examples = "\n".join(
        f'Headline: "{ex["headline"]}"\nEntities: {ex["entities"]}\n'
        for ex in FEW_SHOT_EXAMPLES
    )

    return f"""{SYSTEM_PROMPT}

Here are some examples:

{examples}
Now extract financial entities from this headline:
Headline: "{headline}"
Entities:"""
