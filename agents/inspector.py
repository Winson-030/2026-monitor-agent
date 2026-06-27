import json
import vertexai
from vertexai.generative_models import GenerativeModel
from agents.prompts import SYSTEM_PROMPT, DEEP_INSPECTION_PROMPT, CHAT_SYSTEM_PROMPT

# Initialize Vertex AI with global region for model availability
vertexai.init(location="global")

# Model mapping by scenario
MODELS = {
    "standard": "gemini-2.5-flash",      # Fast, cost-effective for routine checks
    "deep": "gemini-2.5-flash",          # Use same model for now (3.1-pro not available in us-central1)
    "chat": "gemini-2.5-flash",           # Quick responses for Telegram Q&A
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


def chat(question: str, report: dict | None) -> str:
    """Natural language chat powered by Gemini 3.5 Flash."""
    print(f"[CHAT] Question: {question}")
    # Build context from latest report
    if report and report.get("results"):
        lines = [f"时间: {report.get('timestamp', '?')}", f"区域: {report.get('zone', '?')}", ""]
        for r in report["results"]:
            a = r.get("analysis", {})
            lines.append(f"{r['id']}: status={a.get('status', '?')}, reason={a.get('reason', '')}, "
                         f"cpu={r.get('cpu', 'N/A')}, memory={r.get('memory', 'N/A')}, disk={r.get('disk', 'N/A')}")
        context = "\n".join(lines)
    else:
        context = "暂无巡检数据"

    print(f"[CHAT] Context: {context[:200]}...")
    model = GenerativeModel(
        MODELS["chat"],
        system_instruction=[CHAT_SYSTEM_PROMPT.format(context=context)],
    )
    response = model.generate_content(question)
    print(f"[CHAT] Response: {response.text[:200]}...")
    return response.text
