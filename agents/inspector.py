import json
import vertexai
from vertexai.generative_models import GenerativeModel
from agents.prompts import SYSTEM_PROMPT, DEEP_INSPECTION_PROMPT

vertexai.init()

# Model mapping by scenario
MODELS = {
    "standard": "gemini-3.5-flash",      # Fast, cost-effective for routine checks
    "deep": "gemini-3.1-pro-preview",     # Advanced reasoning for deep analysis
    "chat": "gemini-3.5-flash",           # Quick responses for Telegram Q&A
}


class Inspector:
    def __init__(self, mode: str = "standard"):
        model_id = MODELS.get(mode, MODELS["standard"])
        prompt = DEEP_INSPECTION_PROMPT if mode == "deep" else SYSTEM_PROMPT
        self.model = GenerativeModel(model_id, system_instruction=[prompt])
        self.mode = mode

    def analyze(self, target: str, metrics: dict) -> dict:
        prompt = f"""资源: {target}
指标: {json.dumps(metrics, indent=2)}
请分析并输出 JSON。"""
        response = self.model.generate_content(prompt)
        return json.loads(response.text)
