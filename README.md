# Interview Agents (Local Multi-Agent System)

Local Python system using LangGraph + Ollama to:
- poll Gmail for interview-related emails,
- extract structured data and store it in Google Sheets,
- generate interview prep docs,
- send a daily SMS/WhatsApp summary.

## Setup

1. Create and activate a Python 3.10+ virtualenv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill values.
4. Ensure Ollama is running locally and your model is available:
   ```bash
   ollama run llama3
   ```
5. Create Google API OAuth credentials (`credentials.json`) with Gmail + Sheets access enabled.

## Sheet schema

The sheet should have this header row (auto-created by code if empty):

`id, sender_name, sender_email, company, role, interview_datetime, meeting_link, subject, snippet, prep_doc, created_at, updated_at`

## Commands

Poll Gmail and process recent emails:
```bash
python -m interview_agents.main poll-gmail --max-results 20
```

Process a local raw email text file:
```bash
python -m interview_agents.main process-email-file /path/to/email.txt
```

Send daily summary notification (SMS or WhatsApp, based on Twilio env config):
```bash
python -m interview_agents.main send-daily-sms
```

Run tests:
```bash
pytest -q
```

## Daily cron at 6pm (local time)

```cron
0 18 * * * cd /Users/sarah9db/Downloads/testAgent && /usr/bin/env python -m interview_agents.main send-daily-sms
```

## Notes

- `poll-gmail` deduplicates based on Gmail message ID in the `id` column.
- If `company` or `role` is missing, the row is treated as not clearly interview-related and is skipped.
- `prep_doc` is stored as markdown text directly in the sheet.
- Daily SMS is incremental. It uses `SMS_LAST_RUN_FILE` (default `.state/last_sms_run.txt`) and sends only rows created/updated since the last successful run. On first run, it falls back to the last 24 hours.
- Notification channel selection:
  - If `TWILIO_WHATSAPP_FROM` and `TWILIO_WHATSAPP_TO` are set, messages are sent via WhatsApp.
  - Otherwise it uses `TWILIO_FROM_NUMBER` and `TWILIO_TO_NUMBER` for SMS.
