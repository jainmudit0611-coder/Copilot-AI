MODEL_RATES = {
    "gpt-4.1-mini": {"prompt": 0.00015 / 1000, "completion": 0.0006 / 1000},
    "gpt-4o": {"prompt": 0.005 / 1000, "completion": 0.015 / 1000},
    "text-embedding-3-small": {"prompt": 0.00002 / 1000, "completion": 0.0},
    "mock": {"prompt": 0.00001 / 1000, "completion": 0.00002 / 1000}
}

class CostCalculator:
    @staticmethod
    def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        rates = MODEL_RATES.get(model, MODEL_RATES["gpt-4o"])
        prompt_cost = prompt_tokens * rates["prompt"]
        completion_cost = completion_tokens * rates["completion"]
        return round(prompt_cost + completion_cost, 6)
