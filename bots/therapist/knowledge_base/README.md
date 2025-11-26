# Therapist Bot Knowledge Base

This directory contains documents that the Therapist bot can reference when answering questions.

## How It Works

1. Documents in this directory can be added to the bot's knowledge base using the `add_document.py` script
2. Each document is chunked into smaller pieces and embedded using Voyage AI
3. When a user asks a question, the bot searches for relevant chunks and uses them to inform its response

## Adding Documents

Use the CLI script to add documents:

```bash
cd /home/user/my-bot-army

python scripts/add_document.py \
  --bot_id therapist \
  --title "Services Overview" \
  --file bots/therapist/knowledge_base/services_overview.txt \
  --source "manual_upload"
```

## Document Format

- **Plain text (.txt)**: Simple, works best for now
- Keep documents focused on specific topics
- Use clear, descriptive titles
- Organize by category (services, insurance, policies, etc.)

## Current Documents

- `services_overview.txt` - Overview of therapy services offered
- `insurance_and_fees.txt` - Payment, insurance, and fee information
- `getting_started.txt` - How to begin therapy at the practice

## Tips for Good Documents

1. **Be specific**: Include actual details (services, approaches, policies)
2. **Be accurate**: Only include current, verified information
3. **Be organized**: Use clear headings and structure
4. **Be complete**: Cover likely client questions
5. **Update regularly**: Keep information current
6. **Maintain privacy**: Never include client information or case details

## Managing Documents

List all documents for this bot:
```bash
python scripts/test_rag.py --bot_id therapist --list
```

Regenerate embeddings (after changing models or chunking):
```bash
python scripts/reindex_bot.py --bot_id therapist
```

## File Organization Suggestions

```
knowledge_base/
├── services/
│   ├── individual_therapy.txt
│   ├── couples_therapy.txt
│   ├── group_therapy.txt
│   └── specialized_programs.txt
├── policies/
│   ├── insurance_and_fees.txt
│   ├── cancellation_policy.txt
│   └── confidentiality.txt
├── approaches/
│   ├── cbt_overview.txt
│   ├── dbt_overview.txt
│   └── eft_overview.txt
└── faqs/
    ├── getting_started.txt
    └── common_questions.txt
```

## Important Notes

- **No PHI**: Never include Protected Health Information (PHI) or client data
- **Current Info Only**: Ensure all information is up-to-date
- **Professional Language**: Maintain professional, compassionate tone
- **Crisis Resources**: Always include current crisis hotline numbers

## Need Help?

See the main project documentation or run:
```bash
python scripts/add_document.py --help
python scripts/test_rag.py --help
```
