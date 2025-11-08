# Environment Configuration Guide

This document explains how to configure environment variables for the Elios AI Interview Service.

## Environment File Priority

The application and scripts read environment variables in the following order:

1. **`.env.local`** (highest priority) - Local overrides, not committed to git
2. **`.env`** (fallback) - Default configuration, can be committed to git
3. **System environment variables** (lowest priority)

This allows you to:
- Keep shared configuration in `.env` (safe to commit without sensitive data)
- Override with local settings in `.env.local` (ignored by git, for sensitive data)
- Use different configurations per developer without conflicts

## Quick Start

### For Development

```bash
# Copy the example file
cp .env.example .env

# Edit with your local database credentials
# Then create .env.local for sensitive overrides
cp .env .env.local

# Edit .env.local with your actual passwords/keys
nano .env.local  # or your editor of choice
```

### For Production

```bash
# Use system environment variables or a secure secrets manager
# Do NOT commit .env files with production credentials
```

## Configuration Files

### `.env.example`
- Template file showing all available configuration options
- **Safe to commit** - contains no sensitive data
- Copy this to `.env` to get started

### `.env`
- Default configuration for the project
- Can be committed if it contains no secrets
- Use placeholder values or non-sensitive defaults
- Good for team-shared configuration

### `.env.local`
- Local developer overrides
- **Never committed** (in `.gitignore`)
- Contains your personal credentials and sensitive data
- Takes precedence over `.env`

## Example Setup

**`.env`** (committed, shared configuration):
```bash
# Shared development configuration
APP_NAME="Elios AI Interview Service"
ENVIRONMENT="development"
DEBUG=true

# Database (use placeholders)
DATABASE_URL="postgresql://elios:CHANGE_ME@localhost:5432/elios_interviews"

# API Keys (use placeholders)
OPENAI_API_KEY="sk-your-key-here"
PINECONE_API_KEY="your-key-here"
```

**`.env.local`** (not committed, personal configuration):
```bash
# Your actual credentials
DATABASE_URL="postgresql://elios:my_secure_password_123@localhost:5432/elios_dev"

# Your actual API keys
OPENAI_API_KEY="sk-real-key-abc123xyz789"
PINECONE_API_KEY="real-pinecone-key-xyz"

# Personal overrides
DEBUG=true
LOG_LEVEL="DEBUG"
```

## Configuration Options

### Application Settings

```bash
APP_NAME="Elios AI Interview Service"
APP_VERSION="0.1.0"
ENVIRONMENT="development"  # development, staging, production
DEBUG=true
```

### API Settings

```bash
API_HOST="0.0.0.0"
API_PORT=8000
API_PREFIX="/api"
```

### Database Settings

**Option 1: Full connection URL (recommended)**
```bash
DATABASE_URL="postgresql://user:password@host:port/database"
```

**Option 2: Individual parameters**
```bash
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432
POSTGRES_USER="elios"
POSTGRES_PASSWORD="your-password"
POSTGRES_DB="elios_interviews"
```

### LLM Provider Settings

```bash
# Provider selection
LLM_PROVIDER="openai"  # openai, claude, llama

# OpenAI
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4"
OPENAI_TEMPERATURE=0.7

# Anthropic Claude (alternative)
ANTHROPIC_API_KEY="sk-ant-..."
ANTHROPIC_MODEL="claude-3-sonnet-20240229"
```

### Vector Database Settings

```bash
VECTOR_DB_PROVIDER="pinecone"  # pinecone, weaviate, chroma

# Pinecone
PINECONE_API_KEY="..."
PINECONE_ENVIRONMENT="us-east-1"
PINECONE_INDEX_NAME="elios-interviews"
```

### Speech Services Settings

```bash
AZURE_SPEECH_KEY="..."
AZURE_SPEECH_REGION="eastus"
```

### File Storage Settings

```bash
UPLOAD_DIR="./uploads"
CV_DIR="./uploads/cvs"
AUDIO_DIR="./uploads/audio"
```

### Interview Configuration

```bash
MAX_QUESTIONS_PER_INTERVIEW=10
MIN_PASSING_SCORE=60.0
QUESTION_TIMEOUT_SECONDS=300
```

### Logging Settings

```bash
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT="json"  # json or text
```

### CORS Settings

```bash
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
```

## Best Practices

### Security

1. **Never commit sensitive data**
   - Use `.env.local` for passwords, API keys, and secrets
   - Keep `.env.local` in `.gitignore`

2. **Use strong passwords**
   - Database passwords should be complex
   - Change default passwords

3. **Rotate API keys regularly**
   - Especially for production environments

4. **Use environment-specific values**
   - Different credentials for dev/staging/production

### Organization

1. **Document all variables**
   - Keep `.env.example` up-to-date
   - Add comments explaining each variable

2. **Group related settings**
   - Keep database settings together
   - Group by service or feature

3. **Use consistent naming**
   - Uppercase with underscores: `DATABASE_URL`
   - Prefix by service: `POSTGRES_`, `OPENAI_`, etc.

### Development Workflow

1. **Initial setup:**
   ```bash
   cp .env.example .env
   cp .env .env.local
   # Edit .env.local with your credentials
   ```

2. **When adding new variables:**
   ```bash
   # Add to .env.example first (with placeholder)
   # Document what it does
   # Then add actual value to your .env.local
   ```

3. **Sharing configuration:**
   ```bash
   # Update .env.example when adding new variables
   # Commit .env.example
   # Tell team to update their .env.local
   ```

## Verification

Check which environment file is being loaded:

```bash
# Run any script - it will print which file it loads
python scripts/setup_db.py

# Output will show:
# Loading environment from: .env.local
# or
# Loading environment from: .env
```

## Troubleshooting

### Problem: Changes not taking effect

**Solution:** Check file priority
```bash
# If .env.local exists, it overrides .env
# Make sure you're editing the right file

# To check which file is active:
ls -la .env*
```

### Problem: "No .env file found"

**Solution:**
```bash
# Create from example
cp .env.example .env

# Or create .env.local
cp .env.example .env.local
```

### Problem: Variables not loading

**Solution:**
```bash
# Check file format (no spaces around =)
# Good:  DATABASE_URL="value"
# Bad:   DATABASE_URL = "value"

# Check for syntax errors
cat .env.local | grep DATABASE_URL
```

### Problem: Git showing .env.local changes

**Solution:**
```bash
# Make sure .env.local is in .gitignore
grep "\.env\.local" .gitignore

# If missing, add it:
echo ".env.local" >> .gitignore
```

## Migration Notes

If you're upgrading from a system that only used `.env`:

1. **Backup your current `.env`:**
   ```bash
   cp .env .env.backup
   ```

2. **Split configuration:**
   ```bash
   # Keep non-sensitive defaults in .env
   # Move sensitive data to .env.local
   ```

3. **Update scripts:**
   - All scripts now automatically check `.env.local` first
   - No changes needed to your workflow

## Related Documentation

- [[DATABASE_SETUP.md]] - Database configuration details
- [[CLAUDE.md]] - Project architecture and structure
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
