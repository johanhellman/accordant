# Seeding Council Personas & System Prompts - Production Fix

**Date**: January 28, 2026  
**Issue**: Default council personas and system prompts were not seeded during deployment

## Problem

The database had:
- **0 council personas** - preventing users from using the council deliberation feature
- **0 system prompts** - missing global default prompts required for council functionality

The seed script exists (`packages/database/scripts/seed-council.ts`) but was never executed during deployment.

## Solution

Created Python scripts to generate SQL INSERT statements from YAML files and executed them:

1. **seed-personas-sql.py** - Parses 16 persona YAML files and generates SQL INSERT statements
2. **seed-system-prompts-sql.py** - Parses `system-prompts.yaml` and generates SQL INSERT statements for 4 system prompts

**Note**: The original seed script (`seed-council.ts`) handles both personas AND system prompts, but neither were seeded because the script was never executed.

## Execution

```bash
# Generate and execute persona seeding
cd /root/apps/accordant
python3 seed-personas-sql.py > /tmp/seed-personas.sql
cat /tmp/seed-personas.sql | docker exec -i ai-stack_db psql -U accordant -d accordant

# Generate and execute system prompts seeding
python3 seed-system-prompts-sql.py > /tmp/seed-system-prompts.sql
cat /tmp/seed-system-prompts.sql | docker exec -i ai-stack_db psql -U accordant -d accordant
```

## Results

- ✅ **16 council personas** seeded (all enabled)
- ✅ **4 system prompts** seeded (global defaults)
- ✅ **4 model providers** represented (Anthropic, OpenAI, Gemini, XAI)

## Personas Seeded

### Anthropic (Claude models)
- The Adversarial Critic
- The Group Operational Pragmatist
- Group Systems Strategist
- The Underlying Principles Analyst

### OpenAI (GPT-4 models)
- The First-Principles Analyst
- The Operational Realist
- The Red-Team Skeptic
- The Systems Strategist

### Gemini (Gemini models)
- The Critical Guardian
- The Pragmatic Operator
- The Structural Architect
- The Systems Synthesizer

### XAI (Grok models)
- The Adversarial Sceptic
- The First-Principles Architect
- The Pragmatic Operator
- The Systems Dynamicist

## System Prompts Seeded

1. `council_base_system_prompt` - Base system prompt for council members
2. `council_ranking_prompt` - Prompt for ranking responses
3. `council_chairman_prompt` - Prompt for council chairman synthesis
4. `council_title_generation` - Prompt for generating council run titles

## Original Seed Script

The original seed script exists at:
- `xmarkdigest/packages/database/scripts/seed-council.ts`

This script should be executed during deployment but wasn't. The Python scripts were created as a workaround to seed the production database.

## Recommendation

Add seed script execution to the deployment process:

```bash
# After migrations
cd xmarkdigest/packages/database
npx tsx scripts/seed-council.ts
```

Or integrate into Dockerfile/startup script.
