# URL Shortener API

A high-performance URL shortening service built with FastAPI, featuring aggressive Redis caching for sub-millisecond redirects and comprehensive click analytics.

**Live Demo:** Status - EC2 Stopped 

---

## Tech Stack

**Backend Framework:**
- FastAPI
- Python 3.12
- Pydantic for validation

**Database & Caching:**
- PostgreSQL 16 (via RDS)
- Redis 7 (via ElastiCache)
- SQLAlchemy ORM
- Alembic for migrations

**Infrastructure:**
- Docker & Docker Compose
- AWS (EC2, RDS, ElastiCache)
- Terraform for Infrastructure as Code
- GitHub Actions for CI/CD

**Authentication:**
- JWT tokens
- bcrypt password hashing

---

## Key Features

### Performance-First Architecture
- **Sub-5ms redirects** with Redis cache-aside pattern
- Cache warming on link creation for instant first access
- Background task processing for non-blocking click recording
- Strategic cache invalidation on updates/deletes

### Link Management
- Random short code generation with collision handling
- Custom short codes with profanity filtering
- Link expiration support
- Full CRUD operations with authorization

### Analytics & Tracking
- Click tracking with referrer, user agent, and IP capture
- Aggregated statistics (total, daily, weekly, monthly)
- Top referrers analysis with GROUP BY queries
- Individual click records for detailed analysis

### Security & Best Practices
- JWT authentication with HTTPBearer
- User-level authorization (users can only manage their own links)
- Password validation (8-72 character limit for bcrypt compatibility)
- Input sanitization and validation
- Environment-based configuration

---

## Architecture Highlights

**Caching Strategy:**
```
Cache Hit Path:  Redis → Redirect (1-2ms, no DB query)
Cache Miss Path: PostgreSQL → Cache → Redirect (5-10ms)
```

**Background Tasks:**
- Click recording happens asynchronously after redirect response
- Prevents blocking the redirect endpoint
- Uses separate database session for safety

**Database Design:**
- Users → Links (one-to-many)
- Links → Clicks (one-to-many, cascade delete)
- Indexed columns for performance (short_code, clicked_at)

---

## Project Structure

```
url-shortener/
├── main.py                # FastAPI app setup
├── routers/
│   ├── auth.py            # Registration, login
│   ├── links.py           # Link CRUD operations
│   └── redirect.py        # Short link redirects with caching
├── db_models.py           # SQLAlchemy models
├── models.py              # Pydantic schemas
├── auth.py                # JWT and password utilities
├── dependencies.py        # FastAPI dependencies
├── db_config.py           # Database configuration
├── redis_config.py        # Redis client setup
├── utils/
│   └── short_code.py      # Short code generation and validation
├── tests/                 # pytest test suite (~13 tests)
├── alembic/               # Database migrations
├── terraform/             # AWS infrastructure
└── Dockerfile             # Production container
```

---

## API Endpoints

### Authentication
- `POST /auth/register` - Create new user account
- `POST /auth/login` - Get JWT token

### Links
- `POST /links` - Create short link (random or custom code)
- `GET /links` - List user's links (paginated)
- `PATCH /links/{id}` - Update link URL or expiration
- `DELETE /links/{id}` - Delete link and invalidate cache

### Redirects
- `GET /{short_code}` - Redirect to original URL (with click tracking)

### Analytics
- `GET /clicks/{link_id}` - Get all clicks for a link
- `GET /clicks/stats` - Aggregated statistics across all user's links

---

## Local Development

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (via Docker)
- Redis (via Docker)

### Setup

```bash
# Clone repository
git clone https://github.com/odysian/url-shortener.git
cd url-shortener

# Start databases
docker-compose up -d

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --port 8000
```

**Access API documentation:** http://localhost:8000/docs

---

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_links.py
```

**Test coverage:** ~13 tests covering authentication, link CRUD, redirects, click tracking, cache behavior, and collision handling.

---

## Deployment

### Infrastructure Setup (Terraform)

```bash
cd terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Deploy to AWS
terraform apply
```

**Infrastructure created:**
- VPC with public/private subnets
- RDS PostgreSQL instance (db.t3.micro)
- ElastiCache Redis cluster (cache.t3.micro)
- EC2 instance (t3.micro)
- Security groups and IAM roles

### CI/CD Pipeline (GitHub Actions) COMING SOON

- **On Pull Request:** Run tests, lint checks
- **On Push to Main:** Deploy to AWS automatically
- **Blue-Green Deployment:** Zero-downtime updates

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Environment
ENVIRONMENT=production
```

---

## Performance Optimizations

**Caching Strategy:**
- Cache-aside pattern for maximum hit rate
- Cache warming on link creation
- JSON serialization for complex data structures
- 5-minute TTL on statistics endpoint

**Database:**
- Indexed columns (short_code, clicked_at, user_id)
- Eager loading to prevent N+1 queries
- Connection pooling via SQLAlchemy

**Query Optimization:**
- Aggregate functions (COUNT, GROUP BY) at database level
- Single JOIN for user click queries
- Pagination support to limit result sets

---

## Design Decisions

### 302 (Temporary) Redirects
Allows click tracking on every request. Browsers don't cache, so analytics remain accurate.

### Random Short Codes
Better security (can't guess other links) compared to sequential encoding. Collision handling ensures uniqueness.

### Cache Warming
Pre-populates cache on creation for instant first redirect. URL shorteners prioritize speed over memory.

### Background Tasks for Clicks
Prevents blocking redirect response. Users get instant redirects while analytics happen asynchronously.

---

## What I Learned

**Performance Optimization:**
- Cache-aside patterns and invalidation strategies
- Background task processing with FastAPI
- Database query optimization with SQLAlchemy
- Redis data structure design

**System Design:**
- High-read, low-write system architecture
- Trade-offs between consistency and performance
- Collision handling with retry logic
- Graceful degradation patterns

**DevOps:**
- ElastiCache Redis deployment and configuration
- Docker multi-stage builds for production
- Terraform for reproducible infrastructure
- Blue-green deployment strategies

---

## Future Enhancements

- [ ] QR code generation for links
- [ ] Geographic analytics with IP geolocation
- [ ] Custom domains support
- [ ] Link preview images (Open Graph)
- [ ] Scheduled link expiration cleanup job
- [ ] Rate limiting per user
- [ ] Link edit history/audit trail

---

## License

MIT

---

## Contact

Chris

- Github: [@odysian](https://github.com/odysian)
- Currently learning: Backend development, building portfolio projects
- Portfolio Project #2 - Building production-grade backend systems
