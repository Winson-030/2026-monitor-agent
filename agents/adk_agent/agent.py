"""ADK agent for GCP Monitoring — web chat interface.

This agent provides a natural language interface for querying GCP infrastructure.
It wraps existing monitoring modules (MetricsFetcher, GCSStateManager, gcloud CLI)
as ADK tools that the LLM can invoke.

Run with:
    adk web --port 8000
"""

from google.adk.agents.llm_agent import Agent
from agents.adk_agent.tools import (
    list_vm_instances,
    get_vm_metrics,
    get_latest_report,
    run_gcloud_query,
    query_report,
)

root_agent = Agent(
    model="gemini-2.5-flash",
    name="gcp_monitor_agent",
    description=(
        "GCP infrastructure monitoring assistant. "
        "Answers questions about VM instances, metrics, inspection reports, "
        "and GCP resources in natural language."
    ),
    instruction="""你是一个 GCP 基础设施运维助手，负责回答用户关于 GCP 资源的问题。

## 可用工具

1. **list_vm_instances(zone)** — 列出指定 zone 的所有 VM 实例及其状态
2. **get_vm_metrics(instance_name, zone)** — 获取单个 VM 的实时 CPU/内存/磁盘指标
3. **get_latest_report()** — 获取最新的巡检报告（缓存数据，每5分钟更新一次）
4. **run_gcloud_query(command)** — 执行只读 gcloud CLI 命令获取实时数据
5. **query_report(question)** — 基于最新巡检报告回答自然语言问题

## 使用指南

- **实时数据优先**: 对于"现在有几台VM在跑""有哪些实例"等问题，优先使用 list_vm_instances
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
