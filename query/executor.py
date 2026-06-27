"""Execute GCP queries using Python client libraries."""

from typing import Optional
from google.cloud import compute_v1
from .intent import QueryIntent


def get_vm_count(project: str, zone: Optional[str] = None, status: Optional[str] = None) -> str:
    """Get the count of VMs, optionally filtered by zone and status."""
    client = compute_v1.InstancesClient()
    
    try:
        if zone:
            request = compute_v1.ListInstancesRequest(
                project=project,
                zone=zone
            )
            vms = client.list(request=request)
            vm_list = [vm for vm in vms]
            
            if status:
                vm_list = [vm for vm in vm_list if vm.status == status]
            
            count = len(vm_list)
            return f"📊 *VM 数量*\n\n区域 `{zone}` 共有 *{count}* 台 VM"
        else:
            # List all zones first
            zones_client = compute_v1.ZonesClient()
            zones_request = compute_v1.ListZonesRequest(project=project)
            zones = zones_client.list(request=zones_request)
            
            total_count = 0
            for zone_obj in zones:
                request = compute_v1.ListInstancesRequest(
                    project=project,
                    zone=zone_obj.name
                )
                vms = client.list(request=request)
                zone_vms = [vm for vm in vms if not status or vm.status == status]
                total_count += len(zone_vms)
            
            return f"📊 *VM 数量*\n\n项目共有 *{total_count}* 台 VM"
    
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def get_vm_list(project: str, zone: Optional[str] = None, status: Optional[str] = None) -> str:
    """Get a formatted list of VMs."""
    client = compute_v1.InstancesClient()
    
    try:
        vm_list = []
        
        if zone:
            request = compute_v1.ListInstancesRequest(
                project=project,
                zone=zone
            )
            vms = client.list(request=request)
            vm_list = [vm for vm in vms if not status or vm.status == status]
        else:
            # List VMs from all zones
            zones_client = compute_v1.ZonesClient()
            zones_request = compute_v1.ListZonesRequest(project=project)
            zones = zones_client.list(request=zones_request)
            
            for zone_obj in zones:
                request = compute_v1.ListInstancesRequest(
                    project=project,
                    zone=zone_obj.name
                )
                vms = client.list(request=request)
                for vm in vms:
                    if not status or vm.status == status:
                        vm.zone = zone_obj.name  # Attach zone info
                        vm_list.append(vm)
        
        if not vm_list:
            return "📝 未找到 VM"
        
        lines = ["🖥️ *VM 列表*\n"]
        lines.append("| 名称 | 状态 | 区域 | 机器类型 |")
        lines.append("|:---|:---|:---|:---|")
        
        for vm in vm_list[:20]:  # Limit to 20 VMs
            name = vm.name or "N/A"
            vm_status = vm.status or "N/A"
            vm_zone = getattr(vm, 'zone', 'N/A').split('/')[-1] if '/' in getattr(vm, 'zone', '') else getattr(vm, 'zone', 'N/A')
            machine_type = vm.machine_type.split('/')[-1] if '/' in (vm.machine_type or '') else (vm.machine_type or "N/A")
            
            status_emoji = {"RUNNING": "🟢", "TERMINATED": "🔴", "STOPPED": "🟡"}.get(vm_status, "⚪")
            
            lines.append(f"| {name} | {status_emoji} {vm_status} | {vm_zone} | {machine_type} |")
        
        if len(vm_list) > 20:
            lines.append(f"\n_还有 {len(vm_list) - 20} 台 VM..._")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def get_vm_status(project: str, target: Optional[str] = None) -> str:
    """Get VM status, optionally for a specific VM."""
    client = compute_v1.InstancesClient()
    
    try:
        vm_list = []
        zones_client = compute_v1.ZonesClient()
        zones_request = compute_v1.ListZonesRequest(project=project)
        zones = zones_client.list(request=zones_request)
        
        for zone_obj in zones:
            request = compute_v1.ListInstancesRequest(
                project=project,
                zone=zone_obj.name
            )
            vms = client.list(request=request)
            for vm in vms:
                if not target or target in vm.name:
                    vm.zone = zone_obj.name
                    vm_list.append(vm)
        
        if not vm_list:
            return "📝 未找到 VM"
        
        if target and len(vm_list) == 1:
            vm = vm_list[0]
            name = vm.name or "N/A"
            status = vm.status or "N/A"
            zone = getattr(vm, 'zone', 'N/A').split('/')[-1] if '/' in getattr(vm, 'zone', '') else getattr(vm, 'zone', 'N/A')
            machine_type = vm.machine_type.split('/')[-1] if '/' in (vm.machine_type or '') else (vm.machine_type or "N/A")
            
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
            running = len([vm for vm in vm_list if vm.status == "RUNNING"])
            terminated = len([vm for vm in vm_list if vm.status == "TERMINATED"])
            stopped = len([vm for vm in vm_list if vm.status == "STOPPED"])
            other = len(vm_list) - running - terminated - stopped
            
            return (
                f"📊 *VM 状态概览*\n\n"
                f"总计: *{len(vm_list)}* 台 VM\n"
                f"🟢 运行中: {running} 台\n"
                f"🔴 已终止: {terminated} 台\n"
                f"🟡 已停止: {stopped} 台\n"
                f"⚪ 其他: {other} 台"
            )
    
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def get_zone_count(project: str) -> str:
    """Get the count of available zones."""
    client = compute_v1.ZonesClient()
    
    try:
        request = compute_v1.ListZonesRequest(project=project)
        zones = client.list(request=request)
        count = sum(1 for _ in zones)
        
        return f"🌍 *可用区数量*\n\n项目共有 *{count}* 个可用区"
    
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def get_resource_summary(project: str) -> str:
    """Get a summary of all resources."""
    try:
        # Get VM count
        instances_client = compute_v1.InstancesClient()
        zones_client = compute_v1.ZonesClient()
        
        zones_request = compute_v1.ListZonesRequest(project=project)
        zones = zones_client.list(request=zones_request)
        
        vm_count = 0
        zone_count = 0
        for zone_obj in zones:
            zone_count += 1
            request = compute_v1.ListInstancesRequest(
                project=project,
                zone=zone_obj.name
            )
            vms = instances_client.list(request=request)
            vm_count += sum(1 for _ in vms)
        
        return (
            f"📋 *资源概览*\n\n"
            f"🖥️ VM 数量: *{vm_count}* 台\n"
            f"🌍 可用区: *{zone_count}* 个\n\n"
            f"使用 */status* 查看详细巡检报告"
        )
    
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


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
