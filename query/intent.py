"""Intent recognition for natural language GCP queries."""

import json
from dataclasses import dataclass
from typing import Optional
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(location="global")

# Supported query types
QUERY_TYPES = [
    "vm_count",           # 有多少台 VM
    "vm_list",            # 列出所有 VM
    "vm_status",          # VM 状态
    "vm_metrics",         # VM 指标（CPU/内存/磁盘）
    "zone_count",         # 有多少个 zone
    "resource_summary",   # 资源汇总
    "unknown",            # 无法识别
]

@dataclass
class QueryIntent:
    """Represents the parsed intent from a user query."""
    query_type: str
    target_resource: Optional[str] = None  # e.g., specific VM name
    filters: dict = None  # e.g., {"status": "RUNNING", "zone": "us-central1-a"}
    original_question: str = ""
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


INTENT_PROMPT = """You are a GCP resource query parser. Parse the user's natural language question and extract the query intent.

Available query types:
- "vm_count": Questions about how many VMs exist (e.g., "有几台 VM", "有多少虚拟机")
- "vm_list": Questions asking to list VMs (e.g., "列出所有 VM", "有哪些虚拟机")
- "vm_status": Questions about VM status (e.g., "VM 状态如何", "哪些 VM 在运行")
- "vm_metrics": Questions about VM metrics (e.g., "CPU 使用率", "内存占用")
- "zone_count": Questions about zones (e.g., "有几个 zone", "可用区")
- "resource_summary": General resource questions (e.g., "资源概况", "整体情况")
- "unknown": Cannot determine intent

Respond ONLY with a JSON object in this format:
{
    "query_type": "one of the types above",
    "target_resource": "specific resource name if mentioned, else null",
    "filters": {
        "status": "RUNNING/TERMINATED/STOPPED if mentioned",
        "zone": "zone name if mentioned"
    }
}

User question: {question}

JSON response:"""


def parse_intent(question: str) -> QueryIntent:
    """Parse user question to extract query intent using LLM.
    
    Args:
        question: User's natural language question
        
    Returns:
        QueryIntent with parsed type, target, and filters
    """
    model = GenerativeModel("gemini-2.5-flash")
    
    prompt = INTENT_PROMPT.format(question=question)
    response = model.generate_content(prompt)
    
    try:
        # Extract JSON from response
        text = response.text.strip()
        # Handle code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(text)
        
        return QueryIntent(
            query_type=result.get("query_type", "unknown"),
            target_resource=result.get("target_resource"),
            filters=result.get("filters", {}),
            original_question=question
        )
    except Exception as e:
        print(f"[ERROR] Failed to parse intent: {e}")
        return QueryIntent(
            query_type="unknown",
            original_question=question
        )
