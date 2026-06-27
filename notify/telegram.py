import json
import requests

def format_report(report: dict | None) -> str:
    if not report:
        return "暂无巡检数据"
    lines = [
        f"📋 巡检报告 ({report.get('timestamp', '?')})",
        f"区域: {report.get('zone', '?')}",
        "---",
    ]
    for r in report.get("results", []):
        analysis = r.get("analysis", {})
        status = analysis.get("status", "unknown")
        icon = {"ok": "✅", "warning": "⚠️", "critical": "🚨"}.get(status, "❓")
        reason = analysis.get("reason", "")
        cpu = r.get("cpu")
        cpu_str = f"CPU: {cpu:.1f}%" if cpu is not None else "CPU: N/A"
        lines.append(f"{icon} {r['id']} | {cpu_str} | {status} | {reason}")
    return "\n".join(lines)

def format_analysis(analysis: dict) -> str:
    status = analysis.get("status", "unknown")
    icon = {"ok": "✅", "warning": "⚠️", "critical": "🚨"}.get(status, "❓")
    reason = analysis.get("reason", "无")
    return f"{icon} 状态: {status}\n原因: {reason}"

def format_alert(findings: list) -> str:
    lines = ["🚨 巡检告警", "---"]
    for f in findings:
        a = f.get("analysis", {})
        lines.append(f"🔴 {f['id']}: {a.get('status', '?')} — {a.get('reason', '')}")
    return "\n".join(lines) if findings else "✅ 无异常"

def answer_question(question: str, report: dict | None) -> str:
    if not report:
        return "暂无巡检数据，无法回答。"
    results = report.get("results", [])
    critical = [r for r in results if r.get("analysis", {}).get("status") == "critical"]
    warning = [r for r in results if r.get("analysis", {}).get("status") == "warning"]
    return (
        f"当前共 {len(results)} 个目标\n"
        f"🚨 critical: {len(critical)} 个\n"
        f"⚠️ warning: {len(warning)} 个\n"
        f"✅ ok: {len(results) - len(critical) - len(warning)} 个\n"
        "---\n"
        f"如需详情，请使用 /status 查看完整报告"
    )


class TelegramHandler:
    def __init__(self, token: str, chat_id: str):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        self.base = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id

    def send_message(self, chat_id: str, text: str):
        try:
            requests.post(
                f"{self.base}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10
            )
        except Exception as e:
            print(f"Telegram send error: {e}")

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
                    "🤖 GCP Monitoring Agent\n\n"
                    "命令:\n"
                    "/status - 查看最新巡检报告\n"
                    "/inspect <vm-name> - 即时查询单台 VM\n"
                    "/help - 显示帮助"
                )
                self.send_message(chat_id, help_text)

            else:
                report = loop.get_latest_report()
                self.send_message(chat_id, answer_question(text, report))
        except Exception as e:
            print(f"Webhook error: {e}")
