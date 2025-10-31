# Database Seeder Skill

A comprehensive Claude Code skill for seeding databases with realistic fake data.

## Installation

### Option 1: Extract Archive
```bash
# Extract the skill archive
tar -xzf db-seeder.tar.gz -C .claude/skills/

# Install dependencies
pip install faker pyyaml sqlalchemy psycopg2-binary
```

### Option 2: Manual Copy
Copy the `db-seeder` directory to your project's `.claude/skills/` folder.

## Quick Start

### 1. Detect Your Database Configuration
```bash
python .claude/skills/db-seeder/scripts/detect_db_config.py
```

### 2. Generate Test Fixtures
```bash
# For Elios project
python .claude/skills/db-seeder/scripts/generate_fixtures.py \
  --template elios-interview \
  --output fixtures/elios_data.json \
  --pretty

# For custom models
python .claude/skills/db-seeder/scripts/generate_fixtures.py \
  --models User:100,Post:500 \
  --output fixtures/test_data.json
```

### 3. Seed Database
```bash
python .claude/skills/db-seeder/scripts/seed_database.py \
  --fixtures fixtures/elios_data.json \
  --db postgresql \
  --connection "postgresql://user:pass@localhost/mydb"
```

## Features

- **Auto-Detection**: Automatically detects database configuration from environment variables, config files, and project structure
- **Multiple Databases**: PostgreSQL, MySQL, SQLite, MongoDB support
- **ORM Integration**: Works with SQLAlchemy, Django ORM, Prisma
- **Faker Integration**: Generate realistic fake data with 100+ data types
- **Flexible Approaches**: JSON fixtures, Python factories, or YAML configuration
- **Production-Ready**: Batch operations, error handling, progress reporting

## Skill Contents

### Scripts
- `seed_database.py` - Main seeding orchestrator
- `detect_db_config.py` - Auto-detect database configuration
- `generate_fixtures.py` - Generate JSON fixtures with Faker

### References
- `database-configs.md` - Database connection patterns and troubleshooting
- `faker-recipes.md` - Common Faker patterns and examples
- `orm-patterns.md` - ORM-specific seeding patterns

### Assets
- `seed-config-template.yaml` - Configuration template
- `fixture-template.json` - JSON fixture template

## Use Cases

1. **Development Setup** - Seed local databases with sample data
2. **Testing** - Create consistent test fixtures for CI/CD
3. **Staging** - Populate staging environments with realistic data
4. **Demo** - Generate demo data for presentations

## Example: Seed Elios Interview System

```bash
# Generate Elios-specific fixtures
python .claude/skills/db-seeder/scripts/generate_fixtures.py \
  --template elios-interview \
  --output fixtures/elios_dev.json \
  --pretty

# Seed database
python .claude/skills/db-seeder/scripts/seed_database.py \
  --fixtures fixtures/elios_dev.json \
  --db postgresql \
  --connection "postgresql://postgres:password@localhost/elios_dev"

# Verify
psql -d elios_dev -c "SELECT COUNT(*) FROM candidates;"
psql -d elios_dev -c "SELECT COUNT(*) FROM questions;"
psql -d elios_dev -c "SELECT COUNT(*) FROM interview_sessions;"
```

## Documentation

See `SKILL.md` for complete documentation including:
- Detailed workflows
- Advanced usage
- Best practices
- Troubleshooting guide
- Integration examples

## Dependencies

### Required
- Python 3.8+
- Faker (`pip install faker`)

### Optional (based on database)
- SQLAlchemy + psycopg2-binary (PostgreSQL)
- SQLAlchemy + pymysql (MySQL)
- pymongo (MongoDB)
- PyYAML (YAML config support)

## Quick Reference

### Common Commands

```bash
# Auto-detect database
python scripts/detect_db_config.py

# Generate fixtures
python scripts/generate_fixtures.py --template elios-interview --output fixtures.json

# Seed database
python scripts/seed_database.py --fixtures fixtures.json --db postgresql --connection "DB_URL"

# Custom locale
python scripts/generate_fixtures.py --template blog --locale ja_JP --output japanese_data.json
```

### Supported Databases

| Database | Connection String Example |
|----------|---------------------------|
| PostgreSQL | `postgresql://user:pass@host:5432/db` |
| MySQL | `mysql://user:pass@host:3306/db` |
| SQLite | `sqlite:///path/to/db.db` |
| MongoDB | `mongodb://user:pass@host:27017/db` |

## Support

For issues or questions:
1. Check `SKILL.md` for detailed documentation
2. Review `references/` for specific topics
3. Check `assets/` for templates

## License

Created for Elios AI Interview Service project.