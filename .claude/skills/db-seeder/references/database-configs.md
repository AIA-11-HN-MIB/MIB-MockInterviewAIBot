# Database Configuration Reference

This reference provides database connection patterns and configuration examples for various database systems.

## PostgreSQL

### Connection String Format
```
postgresql://username:password@host:port/database
```

### Environment Variables
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/elios_dev
# Or individual components
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=elios_dev
DB_USER=postgres
DB_PASSWORD=password
```

### SQLAlchemy Configuration
```python
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:password@localhost:5432/elios_dev')
```

### Default Port
`5432`

## MySQL / MariaDB

### Connection String Format
```
mysql://username:password@host:port/database
```

### Environment Variables
```bash
DATABASE_URL=mysql://root:password@localhost:3306/elios_dev
# Or individual components
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=elios_dev
DB_USER=root
DB_PASSWORD=password
```

### SQLAlchemy Configuration
```python
from sqlalchemy import create_engine

engine = create_engine('mysql://root:password@localhost:3306/elios_dev')
```

### Default Port
`3306`

## SQLite

### Connection String Format
```
sqlite:///path/to/database.db
# Or for in-memory database
sqlite:///:memory:
```

### Environment Variables
```bash
DATABASE_URL=sqlite:///./elios_dev.db
# Or
DB_TYPE=sqlite
DB_PATH=./elios_dev.db
```

### SQLAlchemy Configuration
```python
from sqlalchemy import create_engine

# File-based
engine = create_engine('sqlite:///./elios_dev.db')

# In-memory
engine = create_engine('sqlite:///:memory:')
```

### Default Port
N/A (file-based database)

## MongoDB

### Connection String Format
```
mongodb://username:password@host:port/database
# With authentication database
mongodb://username:password@host:port/database?authSource=admin
```

### Environment Variables
```bash
MONGODB_URI=mongodb://admin:password@localhost:27017/elios_dev
# Or individual components
DB_TYPE=mongodb
DB_HOST=localhost
DB_PORT=27017
DB_NAME=elios_dev
DB_USER=admin
DB_PASSWORD=password
```

### PyMongo Configuration
```python
from pymongo import MongoClient

client = MongoClient('mongodb://admin:password@localhost:27017/')
db = client['elios_dev']
```

### Default Port
`27017`

## Configuration File Patterns

### .env File
```bash
# PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/elios_dev

# MySQL
DATABASE_URL=mysql://root:password@localhost:3306/elios_dev

# SQLite
DATABASE_URL=sqlite:///./elios_dev.db

# MongoDB
MONGODB_URI=mongodb://admin:password@localhost:27017/elios_dev
```

### settings.py (Pydantic)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    db_type: str = "postgresql"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "elios_dev"
    db_user: str = "postgres"
    db_password: str = ""

    class Config:
        env_file = ".env"
```

### config.yaml
```yaml
database:
  type: postgresql
  host: localhost
  port: 5432
  name: elios_dev
  user: postgres
  password: password
```

### alembic.ini (SQLAlchemy Migrations)
```ini
[alembic]
sqlalchemy.url = postgresql://postgres:password@localhost:5432/elios_dev
```

## Docker Compose Configuration

### PostgreSQL
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: elios_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Connection string: `postgresql://postgres:password@localhost:5432/elios_dev`

### MySQL
```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: elios_dev
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

Connection string: `mysql://root:password@localhost:3306/elios_dev`

### MongoDB
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:6
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
      MONGO_INITDB_DATABASE: elios_dev
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

Connection string: `mongodb://admin:password@localhost:27017/elios_dev`

## Connection String Security

### Best Practices

1. **Never commit connection strings with credentials to version control**
   - Use `.env` files (add to `.gitignore`)
   - Use environment variables
   - Use secret management systems (AWS Secrets Manager, HashiCorp Vault)

2. **Use connection string encoding for special characters**
   ```python
   from urllib.parse import quote_plus

   password = "p@ssw0rd!"
   encoded = quote_plus(password)  # "p%40ssw0rd%21"
   connection = f"postgresql://user:{encoded}@localhost/db"
   ```

3. **Use SSL/TLS for remote connections**
   ```
   # PostgreSQL with SSL
   postgresql://user:pass@host/db?sslmode=require

   # MySQL with SSL
   mysql://user:pass@host/db?ssl-mode=REQUIRED

   # MongoDB with SSL
   mongodb://user:pass@host/db?ssl=true
   ```

4. **Rotate credentials regularly**

5. **Use least-privilege database users**
   - Create separate users for seeding vs. production
   - Limit permissions to only what's needed

## Common Issues and Solutions

### PostgreSQL Connection Refused
```
Error: connection refused
```
**Solutions:**
- Check if PostgreSQL is running: `pg_isready`
- Verify port: `5432` (default)
- Check `pg_hba.conf` for connection permissions
- Ensure firewall allows connection

### MySQL Access Denied
```
Error: Access denied for user 'root'@'localhost'
```
**Solutions:**
- Verify username/password
- Check MySQL user permissions: `SHOW GRANTS FOR 'root'@'localhost';`
- Reset password if needed

### SQLite Database Locked
```
Error: database is locked
```
**Solutions:**
- Close other connections to the database
- Use `sqlite3` CLI to check: `.databases`
- Restart the application

### MongoDB Authentication Failed
```
Error: Authentication failed
```
**Solutions:**
- Verify `authSource` parameter (usually `admin`)
- Check user exists: `db.getUsers()` in mongo shell
- Ensure correct database in connection string

## Detection Script Usage

The `detect_db_config.py` script automatically detects database configuration:

```bash
# Auto-detect from environment and config files
python scripts/detect_db_config.py

# Specify config file
python scripts/detect_db_config.py --config-path src/infrastructure/config/settings.py

# Specify .env file
python scripts/detect_db_config.py --env-file .env

# Specify project root
python scripts/detect_db_config.py --project-root /path/to/project
```

The script will output:
- Detected database type
- Connection details (with masked password)
- Ready-to-use command for `seed_database.py`