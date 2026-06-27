import json
import vertexai
from vertexai.generative_models import GenerativeModel
from agents.prompts import SYSTEM_PROMPT

vertexai.init()

class Inspector:
    MODEL = "gemini-2.5-flash"

    def __init__(self):
        self.model = GenerativeModel(
            self.MODEL,
            system_instruction=[SYSTEM_PROMPT],
        )

    def analyze(self, target: str, metrics: dict) -> dict:
        prompt = f"""资源: {target}
指标: {json.dumps(metrics, indent=2)}
请分析并输出 JSON。"""
        response = self.model.generate_content(prompt)
        return json.loads(response.text)
