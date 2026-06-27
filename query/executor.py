"""Execute gcloud commands to fetch GCP resource data."""

import json
import subprocess
from typing import Any, Optional
from .intent import QueryIntent


def run_gcloud_command(args: list[str], project: str) -> tuple[bool, Any]:
    """Execute a gcloud command and return parsed JSON output.
    
    Args:
        args: List of gcloud command arguments
        project: GCP project ID
        
    Returns:
        Tuple of (success, result) where result is parsed JSON or error message
    """
    cmd = ["gcloud"] + args + ["--project", project, "--format", "json", "--quiet"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return False, f"gcloud command failed: {error_msg}"
        
        if not result.stdout.strip():
            return True, []
        
        return True, json.loads(result.stdout)
    
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 30 seconds"
    except json.JSONDecodeError:
        return False, f"Failed to parse JSON output: {result.stdout[:200]}"
    except Exception as e:
        return False, f"Error executing command: {str(e)}"


def get_vm_count(project: str, zone: Optional[str] = None, status: Optional[str] = None) -> str:
    """Get the count of VMs, optionally filtered by zone and status."""
    args = ["compute", "instances", "list"]
    
    if zone:
        args.extend(["--zones", zone])
    
    if status:
        args.extend(["--filter", f"status:{status}"])
    
    success, result = run_gcloud_command(args, project)
    
    if not success:
        return f"❌ 查询失败: {result}"
    
    vm_list = result if isinstance(result, list) else []
    count = len(vm_list)
    
    if zone:
        return f"📊 *VM 数量*\n\n区域 `{zone}` 共有 *{count}* 台 VM"
    else:
        return f"📊 *VM 数量*\n\n项目共有 *{count}* 台 VM"


def get_vm_list(project: str, zone: Optional[str] = None, status: Optional[str] = None) -> str:
    """Get a formatted list of VMs."""
    args = ["compute", "instances", "list"]
    
    if zone:
        args.extend(["--zones", zone])
    
    if status:
        args.extend(["--filter", f"status:{status}"])
    
    success, result = run_gcloud_command(args, project)
    
    if not success:
        return f"❌ 查询失败: {result}"
    
    vm_list = result if isinstance(result, list) else []
    
    if not vm_list:
        return "📝 未找到 VM"
    
    lines = ["🖥️ *VM 列表*\n"]
    lines.append("| 名称 | 状态 | 区域 | 机器类型 |")
    lines.append("|:---|:---|:---|:---|")
    
    for vm in vm_list[:20]:  # Limit to 20 VMs
        name = vm.get("name", "N/A")
        vm_status = vm.get("status", "N/A")
        vm_zone = vm.get("zone", "").split("/")[-1] if "/" in vm.get("zone", "") else vm.get("zone", "N/A")
        machine_type = vm.get("machineType", "").split("/")[-1] if "/" in vm.get("machineType", "") else vm.get("machineType", "N/A")
        
        status_emoji = {"RUNNING": "🟢", "TERMINATED": "🔴", "STOPPED": "🟡"}.get(vm_status, "⚪")
        
        lines.append(f"| {name} | {status_emoji} {vm_status} | {vm_zone} | {machine_type} |")
    
    if len(vm_list) > 20:
        lines.append(f"\n_还有 {len(vm_list) - 20} 台 VM..._")
    
    return "\n".join(lines)


def get_vm_status(project: str, target: Optional[str] = None) -> str:
    """Get VM status, optionally for a specific VM."""
    args = ["compute", "instances", "list"]
    
    if target:
        args.extend(["--filter", f"name:{target}"])
    
    success, result = run_gcloud_command(args, project)
    
    if not success:
        return f"❌ 查询失败: {result}"
    
    vm_list = result if isinstance(result, list) else []
    
    if not vm_list:
        return "📝 未找到 VM"
    
    if target and len(vm_list) == 1:
        vm = vm_list[0]
        name = vm.get("name", "N/A")
        status = vm.get("status", "N/A")
        zone = vm.get("zone", "").split("/")[-1] if "/" in vm.get("zone", "") else vm.get("zone", "N/A")
        machine_type = vm.get("machineType", "").split("/")[-1] if "/" in vm.get("machineType", "") else vm.get("machineType", "N/A")
        
        status_emoji = {"RUNNING": "🟢", "TERMINATED": "🔴", "STOPPED": "🟡"}.get(status, "⚪")
        
        return (
            f"🖥️ *VM 状态*\n\n"
            f"*名称*: `{name}`\n"
            f"*状态*: {status_emoji} {status}\n"
            f"*区域*: `{zone}`\n"
            f"*机器类型*: `{machine_type}`"
        )
    else:
        # Summary of all VMs
        running = len([vm for vm in vm_list if vm.get("status") == "RUNNING"])
        terminated = len([vm for vm in vm_list if vm.get("status") == "TERMINATED"])
        stopped = len([vm for vm in vm_list if vm.get("status") == "STOPPED"])
        other = len(vm_list) - running - terminated - stopped
        
        return (
            f"📊 *VM 状态概览*\n\n"
            f"总计: *{len(vm_list)}* 台 VM\n"
            f"🟢 运行中: {running} 台\n"
            f"🔴 已终止: {terminated} 台\n"
            f"🟡 已停止: {stopped} 台\n"
            f"⚪ 其他: {other} 台"
        )


def get_zone_count(project: str) -> str:
    """Get the count of available zones."""
    args = ["compute", "zones", "list"]
    
    success, result = run_gcloud_command(args, project)
    
    if not success:
        return f"❌ 查询失败: {result}"
    
    zone_list = result if isinstance(result, list) else []
    count = len(zone_list)
    
    return f"🌍 *可用区数量*\n\n项目共有 *{count}* 个可用区"


def get_resource_summary(project: str) -> str:
    """Get a summary of all resources."""
    # Get VM count
    success, vm_result = run_gcloud_command(
        ["compute", "instances", "list"],
        project
    )
    vm_count = len(vm_result) if success and isinstance(vm_result, list) else 0
    
    # Get zone count
    success, zone_result = run_gcloud_command(
        ["compute", "zones", "list"],
        project
    )
    zone_count = len(zone_result) if success and isinstance(zone_result, list) else 0
    
    return (
        f"📋 *资源概览*\n\n"
        f"🖥️ VM 数量: *{vm_count}* 台\n"
        f"🌍 可用区: *{zone_count}* 个\n\n"
        f"使用 */status* 查看详细巡检报告"
    )


def execute_query(intent: QueryIntent, project: str) -> str:
    """Execute the query based on parsed intent.
    
    Args:
        intent: Parsed query intent
        project: GCP project ID
        
    Returns:
        Formatted response string
    """
    query_type = intent.query_type
    filters = intent.filters or {}
    zone = filters.get("zone")
    status = filters.get("status")
    
    if query_type == "vm_count":
        return get_vm_count(project, zone, status)
    
    elif query_type == "vm_list":
        return get_vm_list(project, zone, status)
    
    elif query_type == "vm_status":
        return get_vm_status(project, intent.target_resource)
    
    elif query_type == "zone_count":
        return get_zone_count(project)
    
    elif query_type == "resource_summary":
        return get_resource_summary(project)
    
    elif query_type == "vm_metrics":
        return (
            "📊 *VM 指标*\n\n"
            "VM 指标数据需要通过巡检报告查看。\n"
            "请使用 */status* 查看最新指标。"
        )
    
    else:
        return (
            "🤔 我不太确定您想查询什么...\n\n"
            "您可以问我：\n"
            "• 有几台 VM？\n"
            "• 列出所有虚拟机\n"
            "• VM 状态如何？\n"
            "• 资源概况"
        )
