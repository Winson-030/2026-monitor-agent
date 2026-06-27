"""ADK tool functions wrapping existing GCP monitoring functionality."""

import json
import subprocess
import shlex
from typing import Optional

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


def init(project_id: str, bucket: str):
    """Initialize the ADK tools with project configuration.

    Args:
        project_id: GCP project ID (e.g., ai-hack-2026-winson)
        bucket: GCS bucket name for inspection reports
    """
    _ensure_initialized(project_id=project_id, bucket=bucket)


# ── ADK Tools ────────────────────────────────────────────────


def list_vm_instances(zone: str = "us-central1-a") -> str:
    """获取指定 zone 的所有 Compute Engine 虚拟机实例及其状态。

    当用户询问"有哪些 VM""列出所有实例""几台机器在运行"时使用此工具。

    Args:
        zone: GCP 区域，例如 us-central1-a, us-central1-b, asia-northeast1-a

    Returns:
        JSON 格式的实例列表，包含名称、状态、机器类型
    """
    _ensure_initialized()
    if _fetcher is None:
        return json.dumps({"error": "MetricsFetcher 未初始化，请先调用 init()"})

    instances = _fetcher.compute.list(project=_project_id, zone=zone)
    results = []
    for inst in instances:
        results.append({
            "name": inst.name,
            "status": inst.status,
            "zone": zone,
            "machine_type": inst.machine_type.split("/")[-1] if inst.machine_type else "unknown",
            "creation_timestamp": inst.creation_timestamp,
        })
    return json.dumps(results, indent=2, default=str)


def get_vm_metrics(instance_name: str, zone: str = "us-central1-a") -> str:
    """获取指定 VM 实例的实时监控指标：CPU 利用率、内存使用率、磁盘使用率。

    当用户询问"某台机器的性能""CPU 使用率""内存占用"时使用此工具。
    注意：内存和磁盘指标需要 VM 安装 Ops Agent。

    Args:
        instance_name: VM 实例的名称
        zone: VM 实例所在的 GCP 区域

    Returns:
        JSON 格式的指标数据，包含 cpu、memory、disk 和状态
    """
    _ensure_initialized()
    if _fetcher is None:
        return json.dumps({"error": "MetricsFetcher 未初始化，请先调用 init()"})

    result = _fetcher.fetch_for_target(instance_name, zone)
    if result is None:
        return json.dumps({
            "error": f"在区域 {zone} 中未找到名为 '{instance_name}' 的实例"
        })
    return json.dumps(result, indent=2, default=str)


def get_latest_report() -> str:
    """获取最新的 GCP 资源巡检报告（缓存在 GCS 中）。

    当用户询问"巡检结果""最新报告""有什么异常"时使用此工具。
    报告由定时任务每5分钟生成一次，包含所有 VM 的状态分析和指标。

    Returns:
        JSON 格式的巡检报告，包含时间戳、各实例状态和分析
    """
    _ensure_initialized()
    if _state is None:
        return json.dumps({"error": "GCS state manager 未初始化，请先调用 init()"})

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

    # ── Safety validations ────────────────────────────────
    blocked_patterns = [
        "create ", "delete ", "update ", "set ", "add ", "remove ",
        "stop ", "start ", "restart ", "ssh ", "scp ", "deploy ",
        "|", "&&", "||", ";", "`", "$(",
    ]
    for pattern in blocked_patterns:
        if pattern in cmd.lower():
            return json.dumps({
                "error": f"命令被安全策略拦截: 禁止包含 '{pattern.strip()}'",
                "allowed": "仅支持只读操作 (list/describe/get)"
            })

    if "--format=json" not in cmd:
        return json.dumps({
            "error": "命令缺少 --format=json 参数",
            "hint": "请添加 --format=json 以确保输出为可解析格式"
        })

    if not cmd.startswith("gcloud "):
        return json.dumps({
            "error": "命令必须以 gcloud 开头",
            "hint": "例如: gcloud compute instances list --format=json"
        })

    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return json.dumps({"error": result.stderr.strip()})
        # Validate JSON output
        try:
            data = json.loads(result.stdout)
            return json.dumps(data, indent=2, default=str)
        except json.JSONDecodeError:
            return result.stdout
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "命令执行超时（30秒）"})
    except FileNotFoundError:
        return json.dumps({"error": "gcloud CLI 未安装或不在 PATH 中"})
    except Exception as e:
        return json.dumps({"error": f"命令执行异常: {str(e)}"})


def query_report(question: str) -> str:
    """基于最新的 GCP 巡检报告，用自然语言回答用户的问题。

    当用户问"报告里有什么问题""哪些机器异常"等需要理解报告内容的问题时使用。
    支持中文和英文提问。

    Args:
        question: 关于巡检数据的问题（支持中文）

    Returns:
        自然语言回答
    """
    _ensure_initialized()
    report = _state.load() if _state else None
    return llm_chat(question, report)
