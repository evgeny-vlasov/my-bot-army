# Keystone Landscaping Knowledge Base

This directory contains documents that the Keystone bot can reference when answering questions.

## How It Works

1. Documents in this directory can be added to the bot's knowledge base using the `add_document.py` script
2. Each document is chunked into smaller pieces and embedded using Voyage AI
3. When a user asks a question, the bot searches for relevant chunks and uses them to inform its response

## Adding Documents

Use the CLI script to add documents:

```bash
cd /home/user/my-bot-army

python scripts/add_document.py \
  --bot_id keystone-landscaping \
  --title "Services Overview" \
  --file bots/keystone-landscaping/knowledge_base/services_overview.txt \
  --source "manual_upload"
```

## Document Format

- **Plain text (.txt)**: Simple, works best for now
- Keep documents focused on specific topics
- Use clear, descriptive titles
- Organize by category (services, pricing, policies, etc.)

## Current Documents

- `services_overview.txt` - Overview of Keystone's landscaping services
- `service_areas.txt` - Geographic coverage information
- `warranty_info.txt` - Warranty and guarantee details

## Tips for Good Documents

1. **Be specific**: Include actual details (prices, areas, services)
2. **Be accurate**: Only include current, verified information
3. **Be organized**: Use clear headings and structure
4. **Be complete**: Cover likely customer questions
5. **Update regularly**: Keep information current

## Managing Documents

List all documents for this bot:
```bash
python scripts/test_rag.py --bot_id keystone-landscaping --list
```

Regenerate embeddings (after changing models or chunking):
```bash
python scripts/reindex_bot.py --bot_id keystone-landscaping
```

## File Organization Suggestions

```
knowledge_base/
├── services/
│   ├── patios.txt
│   ├── retaining_walls.txt
│   ├── outdoor_kitchens.txt
│   └── snow_removal.txt
├── policies/
│   ├── warranty.txt
│   ├── service_areas.txt
│   └── scheduling.txt
├── pricing/
│   ├── residential_rates.txt
│   └── commercial_rates.txt
└── faqs/
    ├── general_questions.txt
    └── seasonal_info.txt
```

## Need Help?

See the main project documentation or run:
```bash
python scripts/add_document.py --help
python scripts/test_rag.py --help
```
