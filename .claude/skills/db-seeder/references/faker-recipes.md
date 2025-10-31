# Faker Recipes and Patterns

Common patterns and examples for generating realistic fake data using the Faker library.

## Basic Usage

```python
from faker import Faker

fake = Faker()

# Generate single value
name = fake.name()
email = fake.email()

# Generate multiple values
names = [fake.name() for _ in range(10)]
```

## Personal Information

### Names
```python
fake.name()                    # "John Smith"
fake.first_name()              # "John"
fake.last_name()               # "Smith"
fake.name_male()               # "Michael Johnson"
fake.name_female()             # "Sarah Williams"
fake.prefix()                  # "Dr."
fake.suffix()                  # "Jr."
```

### Contact Information
```python
fake.email()                   # "john.smith@example.com"
fake.safe_email()              # "john.smith@example.org" (safe domains)
fake.company_email()           # "john.smith@company.com"
fake.phone_number()            # "+1-555-123-4567"
fake.address()                 # "123 Main St, Springfield, IL 62701"
fake.street_address()          # "123 Main St"
fake.city()                    # "Springfield"
fake.state()                   # "Illinois"
fake.zipcode()                 # "62701"
fake.country()                 # "United States"
```

## Business Data

### Company Information
```python
fake.company()                 # "Tech Corp Inc."
fake.company_suffix()          # "Inc."
fake.job()                     # "Software Engineer"
fake.bs()                      # "synergize innovative solutions" (business speak)
fake.catch_phrase()            # "Innovative solutions for tomorrow"
```

## Technical Data

### Internet and URLs
```python
fake.url()                     # "https://example.com"
fake.uri()                     # "/path/to/resource"
fake.domain_name()             # "example.com"
fake.ipv4()                    # "192.168.1.1"
fake.ipv6()                    # "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
fake.mac_address()             # "00:1B:44:11:3A:B7"
fake.user_agent()              # "Mozilla/5.0 ..."
fake.slug()                    # "this-is-a-slug"
```

### File and Storage
```python
fake.file_name()               # "document.pdf"
fake.file_extension()          # "pdf"
fake.mime_type()               # "application/pdf"
fake.file_path()               # "/home/user/document.pdf"
fake.uuid4()                   # "550e8400-e29b-41d4-a716-446655440000"
```

### Colors and Images
```python
fake.color_name()              # "Red"
fake.hex_color()               # "#FF5733"
fake.rgb_color()               # "rgb(255, 87, 51)"
fake.image_url()               # "https://picsum.photos/640/480"
```

## Dates and Times

```python
from datetime import datetime, timedelta

# Random dates
fake.date()                                    # "2023-05-15"
fake.date_of_birth(minimum_age=18, maximum_age=70)  # Date object
fake.date_time()                               # datetime object
fake.date_between(start_date='-1y', end_date='today')  # Within last year
fake.date_time_between(start_date='-30d', end_date='now')  # Last 30 days

# Specific formats
fake.date_time_this_month()
fake.date_time_this_year()
fake.future_date()             # Future date
fake.past_date()               # Past date

# Time components
fake.time()                    # "14:30:45"
fake.timezone()                # "America/New_York"
```

## Text Generation

```python
# Words and sentences
fake.word()                    # "example"
fake.words(nb=5)               # ["word1", "word2", ...]
fake.sentence()                # "This is a sentence."
fake.sentence(nb_words=10)     # Sentence with 10 words
fake.sentences(nb=3)           # List of 3 sentences

# Paragraphs
fake.paragraph()               # Single paragraph
fake.paragraph(nb_sentences=5) # Paragraph with 5 sentences
fake.paragraphs(nb=3)          # List of 3 paragraphs
fake.text(max_nb_chars=200)    # Text up to 200 characters

# Lorem ipsum
fake.text()                    # Lorem ipsum text
```

## Numbers and Data

```python
# Random numbers
fake.random_int(min=0, max=100)          # Integer between 0-100
fake.random_number(digits=5)             # 5-digit number
fake.random_digit()                      # 0-9
fake.pyfloat(left_digits=3, right_digits=2)  # 123.45

# Boolean
fake.boolean()                           # True or False
fake.boolean(chance_of_getting_true=75)  # 75% chance of True

# Sequences
fake.random_element(['A', 'B', 'C'])     # Pick one
fake.random_elements(['A', 'B', 'C'], length=2, unique=True)  # Pick 2 unique

# Credit cards
fake.credit_card_number()
fake.credit_card_expire()
fake.credit_card_provider()
```

## Localization

```python
# Create Faker with specific locale
fake_us = Faker('en_US')
fake_uk = Faker('en_GB')
fake_fr = Faker('fr_FR')
fake_ja = Faker('ja_JP')
fake_vi = Faker('vi_VN')       # Vietnamese

# Examples
fake_us.phone_number()         # US format: +1-555-123-4567
fake_uk.phone_number()         # UK format: 01234 567890
fake_fr.name()                 # French name: Jean Dupont
fake_ja.address()              # Japanese address: 東京都...
fake_vi.name()                 # Vietnamese name: Nguyễn Văn An
fake_vi.phone_number()         # Vietnamese format: +84 912 345 678
fake_vi.address()              # Vietnamese address: 123 Nguyễn Huệ, Hà Nội

# Multiple locales
fake = Faker(['en_US', 'en_GB', 'fr_FR'])  # Random from all
```

### Vietnamese Locale (vi_VN)

Faker supports Vietnamese data generation for creating localized test data:

```python
from faker import Faker

fake_vi = Faker('vi_VN')

# Personal information
fake_vi.name()                 # "Nguyễn Văn An", "Trần Thị Bình"
fake_vi.first_name()           # "Văn", "Thị"
fake_vi.last_name()            # "Nguyễn", "Trần", "Lê"
fake_vi.phone_number()         # "+84 912 345 678", "0987654321"

# Addresses
fake_vi.address()              # "123 Nguyễn Huệ, Quận 1, Hồ Chí Minh"
fake_vi.city()                 # "Hà Nội", "Hồ Chí Minh", "Đà Nẵng"
fake_vi.street_address()       # "456 Lê Lợi"

# Company names (Vietnamese style)
fake_vi.company()              # "Công ty TNHH ABC"
```

**Vietnamese-specific customizations for Elios:**

```python
from faker import Faker

fake_vi = Faker('vi_VN')

# Vietnamese universities
vietnamese_universities = [
    'Đại học Bách Khoa Hà Nội',
    'Đại học Quốc gia Hà Nội',
    'Đại học FPT',
    'Đại học Công nghệ',
    'Đại học Kinh tế Quốc dân',
    'Đại học Ngoại thương',
    'Đại học Bách Khoa TP.HCM',
    'Đại học Quốc gia TP.HCM',
    'Đại học Khoa học Tự nhiên',
    'Đại học Sư phạm Hà Nội',
]

# Vietnamese degrees
vietnamese_degrees = ['Cử nhân', 'Thạc sĩ', 'Tiến sĩ']

# Vietnamese majors
vietnamese_majors = [
    'Khoa học Máy tính',
    'Kỹ thuật Phần mềm',
    'Công nghệ Thông tin',
    'Khoa học Dữ liệu',
    'An toàn Thông tin',
    'Trí tuệ Nhân tạo',
]

# Interview statuses in Vietnamese
vietnamese_statuses = ['đang chờ', 'đã phỏng vấn', 'đã tuyển', 'đã từ chối']

# Generate Vietnamese candidate
def vietnamese_candidate_factory(fake, index):
    return {
        'full_name': fake.name(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'years_of_experience': fake.random_int(min=0, max=15),
        'skills': fake.random_elements(
            ['Python', 'JavaScript', 'SQL', 'React', 'Docker'],
            length=fake.random_int(min=2, max=5),
            unique=True
        ),
        'education': {
            'degree': fake.random_element(vietnamese_degrees),
            'major': fake.random_element(vietnamese_majors),
            'university': fake.random_element(vietnamese_universities),
            'graduation_year': fake.random_int(min=2015, max=2024),
        },
        'address': fake.address(),
        'city': fake.city(),
        'status': fake.random_element(vietnamese_statuses),
        'created_at': fake.date_time_between(start_date='-1y', end_date='now'),
    }
```

## Custom Providers

```python
from faker import Faker
from faker.providers import BaseProvider

class TechSkillProvider(BaseProvider):
    def programming_language(self):
        languages = ['Python', 'JavaScript', 'Java', 'C++', 'Go', 'Rust']
        return self.random_element(languages)

    def framework(self):
        frameworks = ['React', 'Vue', 'Angular', 'Django', 'FastAPI', 'Flask']
        return self.random_element(frameworks)

fake = Faker()
fake.add_provider(TechSkillProvider)

fake.programming_language()    # "Python"
fake.framework()               # "React"
```

## Database Seeding Patterns

### User Factory
```python
def user_factory(fake, index):
    return {
        'id': index + 1,
        'username': fake.user_name(),
        'email': fake.email(),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'password_hash': fake.sha256(),
        'created_at': fake.date_time_between(start_date='-2y', end_date='now'),
        'is_active': fake.boolean(chance_of_getting_true=80),
        'last_login': fake.date_time_between(start_date='-30d', end_date='now'),
    }
```

### Product Factory
```python
def product_factory(fake, index):
    return {
        'id': index + 1,
        'name': ' '.join(fake.words(nb=3)).title(),
        'slug': fake.slug(),
        'description': fake.paragraph(nb_sentences=5),
        'price': fake.pyfloat(left_digits=3, right_digits=2, min_value=10, max_value=1000),
        'stock': fake.random_int(min=0, max=500),
        'sku': fake.bothify(text='???-####', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
        'category': fake.random_element(['Electronics', 'Clothing', 'Books', 'Home']),
        'created_at': fake.date_time_between(start_date='-1y', end_date='now'),
    }
```

### Interview Candidate Factory (Elios-specific)
```python
def candidate_factory(fake, index):
    skills_pool = [
        'Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'MongoDB',
        'Docker', 'Kubernetes', 'AWS', 'Git', 'REST APIs', 'GraphQL',
    ]

    return {
        'id': index + 1,
        'full_name': fake.name(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'years_of_experience': fake.random_int(min=0, max=15),
        'skills': fake.random_elements(skills_pool, length=fake.random_int(min=2, max=6), unique=True),
        'education_degree': fake.random_element(['Bachelor', 'Master', 'PhD']),
        'education_major': 'Computer Science',
        'university': fake.company() + ' University',
        'graduation_year': fake.random_int(min=2010, max=2024),
        'cv_url': f"s3://bucket/cvs/candidate_{index+1}.pdf",
        'linkedin_url': f"https://linkedin.com/in/{fake.user_name()}",
        'created_at': fake.date_time_between(start_date='-6m', end_date='now'),
        'status': fake.random_element(['pending', 'interviewed', 'hired', 'rejected']),
    }
```

### Question Factory (Elios-specific)
```python
def question_factory(fake, index):
    categories = ['technical', 'behavioral', 'system-design', 'coding']
    difficulties = ['easy', 'medium', 'hard']

    return {
        'id': index + 1,
        'text': fake.sentence(nb_words=10) + '?',
        'category': fake.random_element(categories),
        'difficulty': fake.random_element(difficulties),
        'related_skill': fake.random_element(['Python', 'JavaScript', 'SQL', 'System Design']),
        'expected_keywords': [fake.word() for _ in range(fake.random_int(min=3, max=8))],
        'model_answer': fake.paragraph(nb_sentences=5),
        'time_limit_minutes': fake.random_element([5, 10, 15, 30]),
        'created_at': fake.date_time_between(start_date='-1y', end_date='now'),
    }
```

## Performance Tips

### Batch Generation
```python
# Efficient: Generate all at once
fake = Faker()
names = [fake.name() for _ in range(1000)]

# Less efficient: Multiple Faker instances
names = [Faker().name() for _ in range(1000)]
```

### Seeding for Reproducibility
```python
from faker import Faker

# Set seed for reproducible data
Faker.seed(12345)
fake = Faker()

# Always generates same values
fake.name()  # Always "John Smith" (example)
```

### Caching Common Values
```python
# Cache commonly used values
fake = Faker()
user_ids = list(range(1, 101))  # 100 user IDs
cities = [fake.city() for _ in range(20)]  # 20 cities

# Reuse cached values
post = {
    'author_id': fake.random_element(user_ids),
    'city': fake.random_element(cities),
}
```

## Common Pitfalls

### 1. Unique Constraint Violations
```python
# Problem: May generate duplicate emails
users = [{'email': fake.email()} for _ in range(100)]

# Solution: Ensure uniqueness
emails = set()
users = []
while len(users) < 100:
    email = fake.email()
    if email not in emails:
        emails.add(email)
        users.append({'email': email})
```

### 2. Foreign Key References
```python
# Problem: Random foreign keys may not exist
post = {
    'author_id': fake.random_int(min=1, max=1000),  # User may not exist
}

# Solution: Use actual existing IDs
existing_user_ids = [1, 2, 3, 4, 5]  # From created users
post = {
    'author_id': fake.random_element(existing_user_ids),
}
```

### 3. Data Type Mismatches
```python
# Problem: String where integer expected
user = {
    'age': fake.random_int(min=18, max=80),  # ✓ Correct
    'age': str(fake.random_int(min=18, max=80)),  # ✗ Wrong if DB expects int
}
```

## Resources

- [Faker Documentation](https://faker.readthedocs.io/)
- [Available Locales](https://faker.readthedocs.io/en/master/locales.html)
- [Standard Providers](https://faker.readthedocs.io/en/master/providers.html)
