"""ADK agent for GCP Monitoring — web chat interface.

This file defines the ADK root_agent and tool functions.
ADK discovers it via agents/__init__.py.

Run locally:
    adk web --port 8000
    # → Open http://localhost:8000, select "gcp_monitor_agent"
"""

import json
import subprocess
import shlex
from typing import Optional

from google.adk.agents.llm_agent import Agent

from fetcher.metrics import MetricsFetcher
from store.state_manager import GCSStateManager
from agents.inspector import chat as llm_chat

# ── Global instances (lazy init) ──────────────────────────────
_fetcher: Optional[MetricsFetcher] = None
_state: Optional[GCSStateManager] = None
_project_id: Optional[str] = None
_bucket_name: Optional[str] = None


def _ensure_initialized(project_id: str = "", bucket: str = ""):
    global _fetcher, _state, _project_id, _bucket_name
    if project_id:
        _project_id = project_id
    if bucket:
        _bucket_name = bucket
    if _fetcher is None and _project_id:
        _fetcher = MetricsFetcher(_project_id)
    if _state is None and _bucket_name:
        _state = GCSStateManager(_bucket_name)


# ── ADK Tool Functions ─────────────────────────────────────


def list_vm_instances(zone: str = "us-central1-a") -> str:
    """获取指定 zone 的所有 Compute Engine 虚拟机实例及其状态。

    当用户询问有哪些 VM、列出所有实例、几台机器在运行时使用此工具。

    Args:
        zone: GCP 区域，例如 us-central1-a, asia-northeast1-a

    Returns:
        JSON 格式的实例列表，包含名称、状态、机器类型
    """
    _ensure_initialized(project_id="ai-hack-2026-winson")
    if _fetcher is None:
        return json.dumps({"error": "MetricsFetcher 未初始化"})
    instances = _fetcher.compute.list(project=_project_id, zone=zone)
    results = [
        {
            "name": inst.name,
            "status": inst.status,
            "zone": zone,
            "machine_type": inst.machine_type.split("/")[-1] if inst.machine_type else "unknown",
        }
        for inst in instances
    ]
    return json.dumps(results, indent=2, default=str)


def get_vm_metrics(instance_name: str, zone: str = "us-central1-a") -> str:
    """获取指定 VM 实例的实时 CPU 利用率、内存使用率、磁盘使用率。

    当用户询问某台机器的性能、CPU 使用率、内存占用时使用此工具。
    注意：内存和磁盘指标需要 VM 安装 Ops Agent。

    Args:
        instance_name: VM 实例的名称
        zone: VM 实例所在的 GCP 区域

    Returns:
        JSON 格式的指标数据，包含 cpu、memory、disk 和状态
    """
    _ensure_initialized(project_id="ai-hack-2026-winson")
    if _fetcher is None:
        return json.dumps({"error": "MetricsFetcher 未初始化"})
    result = _fetcher.fetch_for_target(instance_name, zone)
    if result is None:
        return json.dumps({"error": f"在区域 {zone} 中未找到名为 '{instance_name}' 的实例"})
    return json.dumps(result, indent=2, default=str)


def get_latest_report() -> str:
    """获取最新的 GCP 资源巡检报告（缓存在 GCS 中）。

    当用户询问巡检结果、最新报告、有什么异常时使用此工具。
    报告由定时任务每 5 分钟生成一次，包含所有 VM 的状态分析和指标。

    Returns:
        JSON 格式的巡检报告，包含时间戳、各实例状态和分析
    """
    _ensure_initialized(bucket="ai-hack-2026-winson-inspection")
    if _state is None:
        return json.dumps({"error": "GCS state manager 未初始化"})
    report = _state.load()
    if report is None:
        return json.dumps({"message": "暂无巡检数据。请等待下次巡检执行。"})
    return json.dumps(report, indent=2, default=str)


def run_gcloud_query(command: str) -> str:
    """执行只读的 gcloud CLI 命令并返回结果。

    当用户需要查询现有工具未覆盖的 GCP 资源（Cloud Run、GKE、SQL 等）时使用。
    此工具只允许 list/describe/get 等只读操作，禁止修改资源的命令。

    Args:
        command: gcloud 命令字符串，必须包含 --format=json

    Returns:
        JSON 格式的命令输出或错误信息
    """
    cmd = command.strip()
    blocked_patterns = [
        "create ", "delete ", "update ", "set ", "add ", "remove ",
        "stop ", "start ", "restart ", "ssh ", "scp ", "deploy ",
        "|", "&&", "||", ";", "`", "$(",
    ]
    for pattern in blocked_patterns:
        if pattern in cmd.lower():
            return json.dumps({
                "error": f"命令被安全策略拦截: 禁止包含 '{pattern.strip()}'",
                "allowed": "仅支持只读操作 (list/describe/get)",
            })
    if "--format=json" not in cmd:
        return json.dumps({"error": "命令缺少 --format=json 参数"})
    if not cmd.startswith("gcloud "):
        return json.dumps({"error": "命令必须以 gcloud 开头"})

    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return json.dumps({"error": result.stderr.strip()})
        data = json.loads(result.stdout)
        return json.dumps(data, indent=2, default=str)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "命令执行超时（30 秒）"})
    except FileNotFoundError:
        return json.dumps({"error": "gcloud CLI 未安装或不在 PATH 中"})
    except Exception as e:
        return json.dumps({"error": f"命令执行异常: {str(e)}"})


def query_report(question: str) -> str:
    """基于最新的 GCP 巡检报告，用自然语言回答用户的问题。

    当用户问报告里有什么问题、哪些机器异常等需要理解报告内容的问题时使用。
    支持中文和英文提问。

    Args:
        question: 关于巡检数据的问题（支持中文）

    Returns:
        自然语言回答
    """
    _ensure_initialized(bucket="ai-hack-2026-winson-inspection")
    report = _state.load() if _state else None
    return llm_chat(question, report)


# ── ADK Agent ──────────────────────────────────────────────

root_agent = Agent(
    model="gemini-2.5-flash",
    name="gcp_monitor_agent",
    description="GCP 基础设施监控助手。可以用自然语言查询 VM 实例、监控指标、巡检报告和 GCP 资源。",
    instruction="""你是一个 GCP 基础设施运维助手，负责回答用户关于 GCP 资源的问题。

## 可用工具

1. **list_vm_instances(zone)** — 列出指定 zone 的所有 VM 实例及其状态
2. **get_vm_metrics(instance_name, zone)** — 获取单个 VM 的实时 CPU/内存/磁盘指标
3. **get_latest_report()** — 获取最新的巡检报告（缓存数据，每 5 分钟更新一次）
4. **run_gcloud_query(command)** — 执行只读 gcloud CLI 命令获取实时数据
5. **query_report(question)** — 基于最新巡检报告回答自然语言问题

## 使用指南

- **实时数据优先**: 对于"现在有几台 VM 在跑""有哪些实例"等问题，优先使用 list_vm_instances
- **指标查询**: 对于特定 VM 的 CPU/内存/磁盘，使用 get_vm_metrics
- **复杂查询**: 如果现有工具不满足需求，使用 run_gcloud_query（如 Cloud Run、GKE 等）
- **巡检报告**: 对于"有什么异常""哪个机器有问题"，使用 get_latest_report 或 query_report

## 安全规则

- run_gcloud_query 只支持只读命令（list/describe/get）
- 不要尝试创建、删除、修改任何 GCP 资源
- 不要执行 ssh/scp 等操作

## 回复风格

- 使用中文回复
- 适当使用 emoji 增强可读性
- 数据较多时用列表或表格呈现
- 如果工具返回错误，礼貌说明原因并给出建议
""",
    tools=[
        list_vm_instances,
        get_vm_metrics,
        get_latest_report,
        run_gcloud_query,
        query_report,
    ],
)
