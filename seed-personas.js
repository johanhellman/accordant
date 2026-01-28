#!/usr/bin/env node
/**
 * Seed Council Personas Script
 * 
 * This script seeds default council personas from YAML files into the database.
 * Run this after database migrations to populate default personas.
 */

const { PrismaClient } = require('@prisma/client');
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const { Pool } = require('pg');
const { PrismaPg } = require('@prisma/adapter-pg');

// Load environment variables
require('dotenv').config({ path: '/root/apps/accordant/.env' });

const connectionString = process.env.DATABASE_URL;
const sslMode = process.env.DATABASE_SSL_MODE;

// Configure SSL for Prisma
let sslConfig = undefined;
if (sslMode === 'no-verify') {
    sslConfig = { rejectUnauthorized: false };
}

const pool = new Pool({
    connectionString,
    ssl: sslConfig,
});

const adapter = new PrismaPg(pool);
const prisma = new PrismaClient({ adapter });

const PERSONALITIES_DIR = path.resolve(
    __dirname,
    'xmarkdigest/packages/council/resources/personalities'
);

async function seedSystemPrompts(data) {
    console.log('Seeding System Prompts...');

    const seedPrompt = async (key, template, variables, model) => {
        const existing = await prisma.promptConfig.findFirst({
            where: {
                key,
                organizationId: null,
            },
        });

        if (existing) {
            console.log(`  ✓ Skipping existing system prompt: ${key}`);
            return;
        }

        await prisma.promptConfig.create({
            data: {
                key,
                organizationId: null,
                template,
                variables: variables || [],
                isDefault: true,
                model: model || 'anthropic/claude-3-sonnet-20240229',
            },
        });
        console.log(`  ✓ Created system prompt: ${key}`);
    };

    if (data.base_system_prompt) {
        const content = typeof data.base_system_prompt === 'string'
            ? data.base_system_prompt
            : data.base_system_prompt.template;
        const model = typeof data.base_system_prompt === 'object' ? data.base_system_prompt.model : undefined;
        await seedPrompt('council_base_system_prompt', content, ['query', 'context'], model);
    }

    if (data.ranking_prompt) {
        const content = typeof data.ranking_prompt === 'string'
            ? data.ranking_prompt
            : data.ranking_prompt.template;
        const model = typeof data.ranking_prompt === 'object' ? data.ranking_prompt.model : undefined;
        await seedPrompt(
            'council_ranking_prompt',
            content,
            ['user_query', 'peer_text', 'responses_text', 'RESPONSE_LABEL_PREFIX', 'FINAL_RANKING_MARKER'],
            model
        );
    }

    if (data.chairman?.prompt) {
        await seedPrompt(
            'council_chairman_prompt',
            data.chairman.prompt,
            ['user_query', 'stage1_text', 'voting_details_text'],
            data.chairman.model
        );
    }

    if (data.title_generation?.prompt) {
        await seedPrompt(
            'council_title_generation',
            data.title_generation.prompt,
            ['user_query'],
            data.title_generation.model
        );
    }
}

async function seedPersona(data) {
    if (!data.id) return;
    
    console.log(`  Seeding Persona: ${data.name} (${data.id})`);

    const existing = await prisma.councilPersona.findUnique({
        where: { id: data.id },
    });

    if (existing) {
        console.log(`    ✓ Skipping existing persona: ${data.name}`);
        return;
    }

    await prisma.councilPersona.create({
        data: {
            id: data.id,
            name: data.name,
            description: data.description || '',
            role: data.ui?.group || 'Council Member',
            avatar: data.ui?.avatar,
            instructions: JSON.stringify(data.personality_prompt),
            model: data.model || 'anthropic/claude-3-sonnet-20240229',
            temperature: data.temperature ?? 0.7,
            isEnabled: data.enabled ?? true,
            checkIn: true,
        },
    });
    console.log(`    ✓ Created persona: ${data.name}`);
}

async function main() {
    console.log(`\n🌱 Seeding Council Personas from ${PERSONALITIES_DIR}...\n`);

    if (!fs.existsSync(PERSONALITIES_DIR)) {
        console.error(`❌ Personalities directory not found: ${PERSONALITIES_DIR}`);
        process.exit(1);
    }

    const files = fs.readdirSync(PERSONALITIES_DIR).filter(f => f.endsWith('.yaml'));

    console.log(`Found ${files.length} YAML files\n`);

    for (const file of files) {
        try {
            const filePath = path.join(PERSONALITIES_DIR, file);
            const content = fs.readFileSync(filePath, 'utf-8');
            const data = yaml.load(content);

            if (file === 'system-prompts.yaml') {
                await seedSystemPrompts(data);
            } else {
                await seedPersona(data);
            }
        } catch (error) {
            console.error(`  ❌ Error processing ${file}:`, error.message);
        }
    }

    const personaCount = await prisma.councilPersona.count();
    const enabledCount = await prisma.councilPersona.count({ where: { isEnabled: true } });
    
    console.log(`\n✅ Seeding completed!`);
    console.log(`   Total personas: ${personaCount}`);
    console.log(`   Enabled personas: ${enabledCount}\n`);
}

main()
    .catch((e) => {
        console.error('❌ Seeding failed:', e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
        await pool.end();
    });
