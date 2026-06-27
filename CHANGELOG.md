
## [v10] - 2026-06-27

### Features
- **Telegram MarkdownV2 Support**: Add proper Markdown formatting for all messages
  - `escape_markdown()`: Escape Telegram MarkdownV2 special characters
  - `send_message()`: Support parse_mode with automatic fallback to plain text
  - `format_report()`: Format reports as Markdown tables with headers
  - `format_analysis()`: Format analysis with Markdown emphasis
  - `format_alert()`: Format alerts with Markdown and emoji
  - `answer_question()`: Format QA responses with Markdown
  - `/help` command: Display help with formatted command list

### Technical
- All messages now use `parse_mode="MarkdownV2"` by default
- Automatic fallback to plain text if MarkdownV2 parsing fails
- VM names and reasons are properly escaped to prevent parsing errors

