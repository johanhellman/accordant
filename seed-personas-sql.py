#!/usr/bin/env python3
"""
Generate SQL INSERT statements for seeding council personas from YAML files.
"""
import yaml
import json
import os
import sys
from pathlib import Path

PERSONALITIES_DIR = Path('/root/apps/accordant/xmarkdigest/packages/council/resources/personalities')

def escape_sql_string(s):
    """Escape single quotes for SQL"""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def generate_persona_sql(data):
    """Generate SQL INSERT for a persona"""
    persona_id = data.get('id')
    name = data.get('name', '')
    description = data.get('description', '')
    role = data.get('ui', {}).get('group', 'Council Member')
    avatar = data.get('ui', {}).get('avatar')
    model = data.get('model', 'anthropic/claude-3-sonnet-20240229')
    temperature = data.get('temperature', 0.7)
    enabled = data.get('enabled', True)
    personality_prompt = data.get('personality_prompt', {})
    
    # Convert personality_prompt to JSON string
    instructions = json.dumps(personality_prompt).replace("'", "''")
    
    sql = f"""
INSERT INTO "CouncilPersona" (
    id, name, description, role, avatar, instructions, model, temperature, 
    "isEnabled", "checkIn", "createdAt", "updatedAt"
) VALUES (
    {escape_sql_string(persona_id)},
    {escape_sql_string(name)},
    {escape_sql_string(description)},
    {escape_sql_string(role)},
    {escape_sql_string(avatar)},
    {escape_sql_string(instructions)},
    {escape_sql_string(model)},
    {temperature},
    {str(enabled).lower()},
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (id) DO NOTHING;
"""
    return sql

def main():
    if not PERSONALITIES_DIR.exists():
        print(f"Error: Directory not found: {PERSONALITIES_DIR}", file=sys.stderr)
        sys.exit(1)
    
    sql_statements = []
    files = sorted([f for f in PERSONALITIES_DIR.glob('*.yaml') if f.name != 'system-prompts.yaml'])
    
    print(f"-- Generated SQL for seeding {len(files)} council personas")
    print(f"-- Generated from: {PERSONALITIES_DIR}\n")
    
    for yaml_file in files:
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            
            if data.get('id'):
                sql = generate_persona_sql(data)
                sql_statements.append(sql)
                print(f"-- Persona: {data.get('name')} ({data.get('id')})")
        except Exception as e:
            print(f"-- Error processing {yaml_file.name}: {e}", file=sys.stderr)
    
    print("\n".join(sql_statements))

if __name__ == '__main__':
    main()
