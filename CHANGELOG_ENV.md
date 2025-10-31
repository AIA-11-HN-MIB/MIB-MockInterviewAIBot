# Environment Configuration Update

## Summary

Updated all migration scripts and configuration to support `.env.local` for local development overrides. This follows security best practices by keeping sensitive credentials out of version control.

## Changes Made

### 1. Updated Scripts

All Python scripts now check for `.env.local` first, then fallback to `.env`:

#### `scripts/setup_db.py`
- Added environment file detection logic
- Prints which file is being loaded
- Tries `.env.local` → `.env` → warns if neither exists

#### `scripts/verify_db.py`
- Same environment loading pattern as setup_db.py
- Consistent behavior across all scripts

#### `scripts/test_env.py` (NEW)
- Test script to verify environment configuration
- Shows which file is active
- Displays loaded settings (with password masking)

### 2. Updated Shell Scripts

#### `scripts/setup_and_migrate.sh` (Linux/macOS)
- Checks for `.env.local` first
- Falls back to `.env`
- Shows which file is being used
- Exports variables from the active file

#### `scripts/setup_and_migrate.bat` (Windows)
- Same logic as bash script
- Windows-compatible syntax
- Sets `ENV_FILE` variable to track active file

### 3. Updated Documentation

#### `.env.example`
- Added header explaining the `.env` vs `.env.local` pattern
- Documents that `.env.local` takes precedence
- Notes that `.env.local` is gitignored

#### `.gitignore`
- Added explicit `.env.local` entry
- Ensures local credentials are never committed

#### `DATABASE_SETUP.md`
- Updated configuration section
- Explains file priority order
- Recommends using `.env.local` for credentials
- Links to new `ENV_SETUP.md`

#### `ENV_SETUP.md` (NEW)
- Comprehensive guide to environment configuration
- Explains priority order
- Best practices for security
- Examples of shared vs. local config
- Troubleshooting guide

## File Priority Order

The application and all scripts now follow this order:

```
1. .env.local (highest priority)
   ↓ if not found
2. .env (fallback)
   ↓ if not found
3. System environment variables
   ↓ if not found
4. Pydantic defaults (from settings.py)
```

## Migration Guide

### For Existing Developers

If you already have a `.env` file:

```bash
# Option 1: Convert .env to .env.local
mv .env .env.local

# Option 2: Keep .env and create .env.local for overrides
cp .env .env.local
# Then edit .env.local with your actual credentials

# Option 3: Just create .env.local from example
cp .env.example .env.local
# Edit with your credentials
```

### For New Developers

```bash
# Copy example to .env.local
cp .env.example .env.local

# Edit with your credentials
nano .env.local
```

## Benefits

1. **Security**
   - Sensitive credentials stay in `.env.local` (gitignored)
   - Safe default configuration in `.env` (can be committed)
   - No accidental credential commits

2. **Flexibility**
   - Each developer can have different local settings
   - Easy to switch between configurations
   - No merge conflicts on environment files

3. **Team Collaboration**
   - Shared defaults in `.env` (optional)
   - Personal overrides in `.env.local`
   - Clear separation of concerns

4. **Consistency**
   - All scripts use the same loading pattern
   - Predictable behavior across the project
   - Clear feedback on which file is active

## Verification

Test the new configuration:

```bash
# Check which environment file will be used
python scripts/test_env.py

# Run database setup (will show which file it loads)
python scripts/setup_db.py

# Run migration scripts
scripts/setup_and_migrate.bat  # Windows
# or
./scripts/setup_and_migrate.sh  # Linux/macOS
```

## Backward Compatibility

This change is **fully backward compatible**:

- Existing `.env` files continue to work
- No changes required to existing workflows
- Scripts gracefully fallback to `.env` if `.env.local` doesn't exist
- Settings.py already supported this pattern via Pydantic

## Configuration Already Supported

The `settings.py` was already configured to use this pattern:

```python
model_config = SettingsConfigDict(
    env_file=(".env.local", ".env"),  # Try .env.local first
    env_file_encoding="utf-8",
    case_sensitive=False,
)
```

This update ensures **all scripts** follow the same pattern.

## Related Files

**Created:**
- `ENV_SETUP.md` - Comprehensive environment configuration guide
- `scripts/test_env.py` - Test script for verifying configuration

**Modified:**
- `scripts/setup_db.py` - Added .env.local support
- `scripts/verify_db.py` - Added .env.local support
- `scripts/setup_and_migrate.sh` - Added .env.local support
- `scripts/setup_and_migrate.bat` - Added .env.local support
- `.env.example` - Added documentation header
- `.gitignore` - Added explicit .env.local entry
- `DATABASE_SETUP.md` - Updated configuration section

**Unchanged:**
- `src/infrastructure/config/settings.py` - Already supported this pattern
- `alembic/env.py` - Uses settings.py, automatically inherits support

## Security Notes

**DO NOT commit:**
- `.env.local` - Personal credentials and sensitive data
- `.env` (if it contains secrets) - Only commit with placeholder values

**Safe to commit:**
- `.env.example` - Template with no sensitive data
- `.env` (optional) - If it contains only non-sensitive defaults

## Questions?

- Read `ENV_SETUP.md` for detailed explanation
- Run `python scripts/test_env.py` to test your configuration
- Check `DATABASE_SETUP.md` for database-specific setup

## Date

Updated: 2025-01-31
