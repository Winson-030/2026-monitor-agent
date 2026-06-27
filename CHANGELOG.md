
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


## [v11] - 2026-06-27

### Features
- **Natural Language GCP Queries**: Ask questions in Chinese and get real-time GCP resource data
  - `query/intent.py`: LLM-based intent recognition using Gemini
  - `query/executor.py`: Real-time VM queries using Google Cloud Python SDK
  - Supported queries: vm_count, vm_list, vm_status, zone_count, resource_summary
  - Automatic fallback to LLM chat for unrecognized queries

### Technical
- Uses `google-cloud-compute` Python client instead of gcloud CLI
- Intent recognition with structured JSON output
- MarkdownV2 formatted responses with tables and emoji

