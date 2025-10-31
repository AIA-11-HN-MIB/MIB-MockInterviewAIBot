# ORM Seeding Patterns

Patterns and best practices for seeding databases using various ORMs (Object-Relational Mappers).

## SQLAlchemy

### Basic Setup

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker

# Create engine and session
engine = create_engine('postgresql://user:pass@localhost/db')
Session = sessionmaker(bind=engine)
session = Session()

fake = Faker()
```

### Simple Seeding

```python
from domain.models import User

# Create single record
user = User(
    username=fake.user_name(),
    email=fake.email(),
    first_name=fake.first_name(),
    last_name=fake.last_name()
)
session.add(user)
session.commit()

# Create multiple records
users = []
for i in range(100):
    user = User(
        username=fake.user_name(),
        email=fake.email(),
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )
    users.append(user)

session.add_all(users)
session.commit()
```

### Batch Seeding for Performance

```python
from domain.models import User

# Batch size for commits
BATCH_SIZE = 1000

users = []
for i in range(10000):
    user = User(
        username=fake.user_name(),
        email=fake.email()
    )
    users.append(user)

    # Commit in batches
    if (i + 1) % BATCH_SIZE == 0:
        session.add_all(users)
        session.commit()
        users = []
        print(f"Committed {i + 1} users")

# Commit remaining
if users:
    session.add_all(users)
    session.commit()
```

### Handling Relationships

```python
from domain.models import User, Post

# Create users first
users = []
for i in range(10):
    user = User(username=fake.user_name(), email=fake.email())
    users.append(user)

session.add_all(users)
session.commit()

# Create posts with foreign key references
posts = []
for i in range(50):
    post = Post(
        title=fake.sentence(),
        content=fake.paragraph(),
        author_id=fake.random_element([u.id for u in users])
    )
    posts.append(post)

session.add_all(posts)
session.commit()
```

### Many-to-Many Relationships

```python
from domain.models import User, Skill

# Create skills
skills = [
    Skill(name='Python'),
    Skill(name='JavaScript'),
    Skill(name='SQL'),
]
session.add_all(skills)
session.commit()

# Create users with skills (many-to-many)
for i in range(20):
    user = User(
        username=fake.user_name(),
        email=fake.email()
    )

    # Add random skills to user
    user_skills = fake.random_elements(
        skills,
        length=fake.random_int(min=1, max=len(skills)),
        unique=True
    )
    user.skills.extend(user_skills)

    session.add(user)

session.commit()
```

### Error Handling

```python
from sqlalchemy.exc import IntegrityError

for i in range(100):
    try:
        user = User(
            username=fake.user_name(),
            email=fake.email()
        )
        session.add(user)
        session.commit()
    except IntegrityError as e:
        # Handle duplicate key violations
        session.rollback()
        print(f"Error creating user {i}: {e}")
```

### Using Factories Pattern

```python
from faker import Faker
from domain.models import User

class UserFactory:
    def __init__(self, session, faker=None):
        self.session = session
        self.fake = faker or Faker()

    def create(self, **kwargs):
        """Create single user"""
        data = {
            'username': self.fake.user_name(),
            'email': self.fake.email(),
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
        }
        data.update(kwargs)

        user = User(**data)
        self.session.add(user)
        self.session.commit()
        return user

    def create_batch(self, count, **kwargs):
        """Create multiple users"""
        users = []
        for _ in range(count):
            data = {
                'username': self.fake.user_name(),
                'email': self.fake.email(),
                'first_name': self.fake.first_name(),
                'last_name': self.fake.last_name(),
            }
            data.update(kwargs)
            users.append(User(**data))

        self.session.add_all(users)
        self.session.commit()
        return users

# Usage
factory = UserFactory(session)
user = factory.create(username='john_doe')
users = factory.create_batch(100, is_active=True)
```

## Django ORM

### Basic Setup

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from myapp.models import User
from faker import Faker

fake = Faker()
```

### Simple Seeding

```python
from myapp.models import User

# Create single record
user = User.objects.create(
    username=fake.user_name(),
    email=fake.email(),
    first_name=fake.first_name(),
    last_name=fake.last_name()
)

# Create multiple records
users = [
    User(
        username=fake.user_name(),
        email=fake.email(),
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )
    for _ in range(100)
]
User.objects.bulk_create(users)
```

### Bulk Operations

```python
from myapp.models import User

# Bulk create (efficient for many records)
users = [User(username=fake.user_name(), email=fake.email()) for _ in range(1000)]
User.objects.bulk_create(users, batch_size=500)

# Get created objects with IDs
users = User.objects.bulk_create(users, batch_size=500)
# Note: In Django 4.0+, bulk_create returns objects with IDs
```

### Relationships

```python
from myapp.models import User, Post

# Create user
user = User.objects.create(username=fake.user_name(), email=fake.email())

# Create posts for user
posts = [
    Post(
        title=fake.sentence(),
        content=fake.paragraph(),
        author=user
    )
    for _ in range(10)
]
Post.objects.bulk_create(posts)
```

### Management Command for Seeding

```python
# myapp/management/commands/seed_database.py

from django.core.management.base import BaseCommand
from faker import Faker
from myapp.models import User

class Command(BaseCommand):
    help = 'Seed database with fake data'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=10)

    def handle(self, *args, **options):
        fake = Faker()
        count = options['users']

        self.stdout.write(f'Creating {count} users...')

        users = [
            User(
                username=fake.user_name(),
                email=fake.email()
            )
            for _ in range(count)
        ]
        User.objects.bulk_create(users)

        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} users'))

# Usage: python manage.py seed_database --users 100
```

## Prisma (TypeScript/JavaScript)

### Basic Setup

```typescript
import { PrismaClient } from '@prisma/client';
import { faker } from '@faker-js/faker';

const prisma = new PrismaClient();
```

### Simple Seeding

```typescript
// Single record
const user = await prisma.user.create({
  data: {
    username: faker.internet.userName(),
    email: faker.internet.email(),
    firstName: faker.person.firstName(),
    lastName: faker.person.lastName(),
  },
});

// Multiple records
const users = await Promise.all(
  Array.from({ length: 100 }, () =>
    prisma.user.create({
      data: {
        username: faker.internet.userName(),
        email: faker.internet.email(),
        firstName: faker.person.firstName(),
        lastName: faker.person.lastName(),
      },
    })
  )
);
```

### Batch Operations

```typescript
// Create many (more efficient)
const users = await prisma.user.createMany({
  data: Array.from({ length: 100 }, () => ({
    username: faker.internet.userName(),
    email: faker.internet.email(),
    firstName: faker.person.firstName(),
    lastName: faker.person.lastName(),
  })),
});
```

### Seeding Script

```typescript
// prisma/seed.ts

import { PrismaClient } from '@prisma/client';
import { faker } from '@faker-js/faker';

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding database...');

  // Create users
  const users = await prisma.user.createMany({
    data: Array.from({ length: 10 }, () => ({
      username: faker.internet.userName(),
      email: faker.internet.email(),
    })),
  });

  console.log(`✓ Created ${users.count} users`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

// Add to package.json:
// "prisma": {
//   "seed": "ts-node prisma/seed.ts"
// }
```

## MongoDB (PyMongo)

### Basic Setup

```python
from pymongo import MongoClient
from faker import Faker

client = MongoClient('mongodb://localhost:27017/')
db = client['mydb']
fake = Faker()
```

### Simple Seeding

```python
# Single document
user = {
    'username': fake.user_name(),
    'email': fake.email(),
    'created_at': fake.date_time()
}
result = db.users.insert_one(user)
print(f"Created user with ID: {result.inserted_id}")

# Multiple documents
users = [
    {
        'username': fake.user_name(),
        'email': fake.email(),
        'created_at': fake.date_time()
    }
    for _ in range(100)
]
result = db.users.insert_many(users)
print(f"Created {len(result.inserted_ids)} users")
```

### With Relationships (Embedded Documents)

```python
# User with embedded posts
user = {
    'username': fake.user_name(),
    'email': fake.email(),
    'posts': [
        {
            'title': fake.sentence(),
            'content': fake.paragraph(),
            'created_at': fake.date_time()
        }
        for _ in range(5)
    ]
}
db.users.insert_one(user)
```

### With References

```python
# Create users first
users = [
    {'username': fake.user_name(), 'email': fake.email()}
    for _ in range(10)
]
user_ids = db.users.insert_many(users).inserted_ids

# Create posts with user references
posts = [
    {
        'title': fake.sentence(),
        'content': fake.paragraph(),
        'author_id': fake.random_element(user_ids)
    }
    for _ in range(50)
]
db.posts.insert_many(posts)
```

## Best Practices

### 1. Transaction Safety

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://user:pass@localhost/db')
Session = sessionmaker(bind=engine)

def seed_database():
    session = Session()
    try:
        # Seeding operations
        users = [User(username=fake.user_name()) for _ in range(100)]
        session.add_all(users)
        session.commit()
        print("✓ Seeding successful")
    except Exception as e:
        session.rollback()
        print(f"✗ Seeding failed: {e}")
        raise
    finally:
        session.close()
```

### 2. Idempotent Seeding

```python
def seed_users(session, count=100):
    # Check if already seeded
    existing_count = session.query(User).count()
    if existing_count >= count:
        print(f"Database already has {existing_count} users, skipping...")
        return

    # Seed remaining
    remaining = count - existing_count
    users = [User(username=fake.user_name()) for _ in range(remaining)]
    session.add_all(users)
    session.commit()
    print(f"✓ Created {remaining} users ({count} total)")
```

### 3. Clearing Before Seeding

```python
def clear_and_seed(session):
    # Clear existing data
    session.query(Post).delete()
    session.query(User).delete()
    session.commit()

    # Seed fresh data
    users = [User(username=fake.user_name()) for _ in range(100)]
    session.add_all(users)
    session.commit()
```

### 4. Seeding with Constraints

```python
def seed_unique_users(session, count=100):
    """Ensure unique usernames/emails"""
    existing_emails = {u.email for u in session.query(User.email).all()}

    users = []
    attempts = 0
    max_attempts = count * 10

    while len(users) < count and attempts < max_attempts:
        email = fake.email()
        if email not in existing_emails:
            user = User(username=fake.user_name(), email=email)
            users.append(user)
            existing_emails.add(email)
        attempts += 1

    session.add_all(users)
    session.commit()
    return len(users)
```

### 5. Progress Reporting

```python
def seed_with_progress(session, count=10000):
    """Seed with progress reporting"""
    batch_size = 1000

    for i in range(0, count, batch_size):
        batch = [
            User(username=fake.user_name(), email=fake.email())
            for _ in range(min(batch_size, count - i))
        ]
        session.add_all(batch)
        session.commit()

        completed = min(i + batch_size, count)
        progress = (completed / count) * 100
        print(f"Progress: {completed}/{count} ({progress:.1f}%)")
```

## Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Django ORM Documentation](https://docs.djangoproject.com/en/stable/topics/db/)
- [Prisma Documentation](https://www.prisma.io/docs/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)