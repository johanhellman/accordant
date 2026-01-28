#!/usr/bin/env python3
"""
Generate SQL INSERT statements for seeding system prompts from YAML.
"""
import yaml
import json
import sys
from pathlib import Path

SYSTEM_PROMPTS_FILE = Path('/root/apps/accordant/xmarkdigest/packages/council/resources/personalities/system-prompts.yaml')

def escape_sql_string(s):
    """Escape single quotes for SQL"""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def generate_prompt_sql(key, template, variables, model=None):
    """Generate SQL INSERT for a system prompt"""
    variables_json = json.dumps(variables or []).replace("'", "''")
    model_value = model or 'anthropic/claude-3-sonnet-20240229'
    
    # Use key as name (required field)
    name = key.replace('_', ' ').replace('council ', '').replace('prompt', 'Prompt')
    
    sql = f"""
INSERT INTO "PromptConfig" (
    id, "organizationId", name, key, template, variables, model, version, "isDefault", 
    "createdAt", "updatedAt"
)
SELECT 
    gen_random_uuid()::text,
    NULL,
    {escape_sql_string(name)},
    {escape_sql_string(key)},
    {escape_sql_string(template)},
    '{variables_json}'::jsonb,
    {escape_sql_string(model_value)},
    1,
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM "PromptConfig" 
    WHERE "organizationId" IS NULL AND key = {escape_sql_string(key)}
);
"""
    return sql

def main():
    if not SYSTEM_PROMPTS_FILE.exists():
        print(f"Error: File not found: {SYSTEM_PROMPTS_FILE}", file=sys.stderr)
        sys.exit(1)
    
    with open(SYSTEM_PROMPTS_FILE, 'r') as f:
        data = yaml.safe_load(f)
    
    print(f"-- Generated SQL for seeding system prompts")
    print(f"-- Generated from: {SYSTEM_PROMPTS_FILE}\n")
    
    sql_statements = []
    
    # Base System Prompt
    if data.get('base_system_prompt'):
        content = data['base_system_prompt']
        if isinstance(content, dict):
            template = content.get('template', '')
            model = content.get('model')
        else:
            template = content
            model = None
        sql = generate_prompt_sql('council_base_system_prompt', template, ['query', 'context'], model)
        sql_statements.append(sql)
        print("-- System Prompt: council_base_system_prompt")
    
    # Ranking Prompt
    if data.get('ranking_prompt'):
        content = data['ranking_prompt']
        if isinstance(content, dict):
            template = content.get('template', '')
            model = content.get('model')
        else:
            template = content
            model = None
        sql = generate_prompt_sql(
            'council_ranking_prompt',
            template,
            ['user_query', 'peer_text', 'responses_text', 'RESPONSE_LABEL_PREFIX', 'FINAL_RANKING_MARKER'],
            model
        )
        sql_statements.append(sql)
        print("-- System Prompt: council_ranking_prompt")
    
    # Chairman Prompt
    if data.get('chairman', {}).get('prompt'):
        sql = generate_prompt_sql(
            'council_chairman_prompt',
            data['chairman']['prompt'],
            ['user_query', 'stage1_text', 'voting_details_text'],
            data['chairman'].get('model')
        )
        sql_statements.append(sql)
        print("-- System Prompt: council_chairman_prompt")
    
    # Title Generation Prompt
    if data.get('title_generation', {}).get('prompt'):
        sql = generate_prompt_sql(
            'council_title_generation',
            data['title_generation']['prompt'],
            ['user_query'],
            data['title_generation'].get('model')
        )
        sql_statements.append(sql)
        print("-- System Prompt: council_title_generation")
    
    print("\n".join(sql_statements))

if __name__ == '__main__':
    main()
