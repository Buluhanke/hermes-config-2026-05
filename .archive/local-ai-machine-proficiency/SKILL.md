---
name: local-ai-machine-proficiency
category: productivity
description: Use when user wants local AI software proficiency.
---

# local-ai-machine-proficiency

## Trigger
Use when the user wants to become proficient with software on their local AI machine, or when they ask to: inventory installed software, research how to use multiple tools, or master a specific application (e.g., WPS).

## Workflow
1. **Inventory** — get the complete picture of what is installed
   - GUI apps: list `/Applications` + look up bundle names
   - CLI tools: `brew list`, `npm ls -g --depth=0`, `pip3 list --format=freeze`
   - Background services: list `~/Library/LaunchAgents/*.plist`
   - Login items: list `~/Library/Application Scripts/*`
2. **Research** — for each major software category, search the web for best practices
   - Use web_search for each category
   - Extract actionable, concrete tips: commands, config keys, keyboard shortcuts, not just feature descriptions
3. **Document** — structure the output for the user
   - Category tables: Software | Type | Usage notes
   - Step-by-step guides for priority software
   - Checklist format for self-assessment
4. **Track** — let the user self-assess what they need to learn

## User Preferences
- Structured, actionable output: tables, checklists, numbered steps — not long narratives
- Comprehensive inventory (not just summary)
- Detail-level varies by software usage frequency
- Personal diary/notes in age-appropriate language when requested
- User's stated priority is WPS mastery ("一定要完全会用") — apply 80/20 rule, focus depth on the highest-value tools

## Pitfalls
- **Overwhelm**: 27 GUI apps + 143+ packages = must prioritize by actual usage frequency, not cover everything equally
- **Vague research**: extract concrete commands and config keys, not just feature descriptions
- **Output verbosity**: use tables and checklists; avoid long narratives
- **Unfocused mastery**: user wants "completely proficient" (完全会用) — this requires deliberate practice, not just reading; include practice exercises

## Self-Assessment Checklist
Includes a per-component checklist the user can use to verify proficiency after learning a tool.