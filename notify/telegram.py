import json
import requests

from agents.inspector import chat as llm_chat


def escape_markdown(text: str) -> str:
    """转义 MarkdownV2 特殊字符
    
    Telegram MarkdownV2 需要转义的字符: _*[]()~`>#+-=|{}.!
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_report(report: dict | None) -> str:
    """格式化巡检报告为 MarkdownV2 格式
    
    Args:
        report: 巡检报告字典
        
    Returns:
        MarkdownV2 格式的报告文本
    """
    if not report:
        return "📋 *巡检报告*\n\n📝 暂无巡检数据"
    
    timestamp = report.get('timestamp', '?')
    zone = report.get('zone', '?')
    results = report.get("results", [])
    
    lines = [
        f"📋 *巡检报告*",
        f"🕐 时间: `{timestamp}`",
        f"🌍 区域: `{zone}`",
        f"🖥️ VM 数量: {len(results)}\n",
        "| VM | CPU | 状态 | 原因 |",
        "|:---|:---|:---|:---|"
    ]
    
    for r in results:
        analysis = r.get("analysis", {})
        status = analysis.get("status", "unknown")
        icon = {"ok": "🟢", "warning": "🟡", "critical": "🔴"}.get(status, "⚪")
        reason = analysis.get("reason", "")
        # 转义 Markdown 特殊字符
        reason = escape_markdown(reason)
        cpu = r.get("cpu")
        cpu_str = f"{cpu:.1f}%" if cpu is not None else "N/A"
        lines.append(f"| {r['id']} | {cpu_str} | {icon} {status} | {reason} |")
    
    return "\n".join(lines)

def format_analysis(analysis: dict) -> str:
    """格式化 AI 分析结果为 MarkdownV2"""
    status = analysis.get("status", "unknown")
    icon = {"ok": "🟢", "warning": "🟡", "critical": "🔴"}.get(status, "⚪")
    reason = analysis.get("reason", "无")
    # 转义 Markdown 特殊字符
    reason = escape_markdown(reason)
    return f"{icon} *状态*: {status}\n📋 *原因*: {reason}"

def format_alert(findings: list) -> str:
    """格式化告警消息为 MarkdownV2"""
    if not findings:
        return "🟢 *状态正常*\n\n暂无告警"
    
    lines = ["🔴 *巡检告警*", ""]
    for f in findings:
        a = f.get("analysis", {})
        status = a.get("status", "?")
        reason = a.get("reason", "")
        # 转义 Markdown 特殊字符
        reason = escape_markdown(reason)
        lines.append(f"🚨 *{f['id']}*: {status}")
        lines.append(f"📋 {reason}")
        lines.append("")
    
    return "\n".join(lines)

def answer_question(question: str, report: dict | None) -> str:
    """格式化问答回复为 MarkdownV2"""
    if not report:
        return "💬 *问题*: " + escape_markdown(question) + "\n\n📝 暂无巡检数据，无法回答。"
    
    results = report.get("results", [])
    critical = [r for r in results if r.get("analysis", {}).get("status") == "critical"]
    warning = [r for r in results if r.get("analysis", {}).get("status") == "warning"]
    ok_count = len(results) - len(critical) - len(warning)
    
    lines = [
        f"💬 *问题*: " + escape_markdown(question),
        "",
        f"📊 *资源概况*:",
        f"🖥️ 总目标: {len(results)} 个",
        f"🔴 critical: {len(critical)} 个",
        f"🟡 warning: {len(warning)} 个",
        f"🟢 ok: {ok_count} 个",
        "",
        f"📋 使用 */status* 查看完整报告"
    ]
    
    return "\n".join(lines)


class TelegramHandler:
    def __init__(self, token: str, chat_id: str):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        self.base = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id

    def send_message(self, chat_id: str, text: str, parse_mode: str = "MarkdownV2"):
        """发送消息到 Telegram
        
        Args:
            chat_id: Telegram chat ID
            text: 消息文本
            parse_mode: 解析模式，默认 MarkdownV2
        """
        url = f"{self.base}/sendMessage"
        
        # 首先尝试发送带格式的消息
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"[WARN] MarkdownV2 send failed, falling back to plain text: {e}")
            
            # 回退到纯文本
            try:
                payload = {
                    "chat_id": chat_id,
                    "text": text
                }
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                return True
            except Exception as e2:
                print(f"[ERROR] Telegram send error: {e2}")
                return False

    def send_alert(self, message: str):
        self.send_message(self.chat_id, message)

    def handle_webhook(self, data: dict, loop):
        try:
            message = data.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "").strip()

            if not text or not chat_id:
                return

            if text == "/status":
                report = loop.get_latest_report()
                self.send_message(chat_id, format_report(report))

            elif text.startswith("/inspect "):
                target = text.replace("/inspect ", "")
                metrics = loop.fetcher.fetch_for_target(target)
                if metrics:
                    analysis = loop.inspector.analyze(target, metrics)
                    self.send_message(chat_id, format_analysis(analysis))
                else:
                    self.send_message(chat_id, f"未找到目标: {target}")

            elif text in ("/start", "/help"):
                help_text = (
                    "🤖 *GCP Monitoring Agent*\n\n"
                    "📋 *可用命令*:\n"
                    "• */status* \\- 查看最新巡检报告\n"
                    "• */inspect* `<vm\\-name>` \\- 即时查询单台 VM\n"
                    "• */help* \\- 显示帮助\n\n"
                    "💬 *自然语言问答*:\n"
                    "直接发送问题，例如：\n"
                    "• 服务器状态怎么样\n"
                    "• CPU 使用率高的 VM 有哪些"
                )
                self.send_message(chat_id, help_text)

            else:
                print(f"[WEBHOOK] Chat message: {text}")
                report = loop.get_latest_report()
                response = llm_chat(text, report)
                print(f"[WEBHOOK] Sending response to {chat_id}")
                # 直接使用 LLM 返回的 Markdown，如果失败会回退到纯文本
                self.send_message(chat_id, response)
        except Exception as e:
            print(f"Webhook error: {e}")
