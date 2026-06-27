import requests


def escape_markdown(text: str) -> str:
    """Escape MarkdownV2 special characters for Telegram."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_alert(findings: list) -> str:
    """Format inspection alerts for Telegram (used by /run-inspection)."""
    if not findings:
        return "🟢 All systems normal — no alerts"
    
    lines = ["🔴 *Inspection Alerts*", ""]
    for f in findings:
        a = f.get("analysis", {})
        status = a.get("status", "?")
        reason = a.get("reason", "")
        reason = escape_markdown(reason)
        lines.append(f"🚨 *{f['id']}*: {status}")
        lines.append(f"📋 {reason}")
        lines.append("")
    
    return "\n".join(lines)


class TelegramHandler:
    def __init__(self, token: str, chat_id: str):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        self.base = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id

    def send_message(self, chat_id: str, text: str, parse_mode: str | None = "MarkdownV2"):
        """Send a message to Telegram.

        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: MarkdownV2 (default), None for plain text
        """
        url = f"{self.base}/sendMessage"
        payload: dict = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"[ERROR] Telegram send error: {e}")
            return False

    def send_alert(self, message: str):
        self.send_message(self.chat_id, message)
