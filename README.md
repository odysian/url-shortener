# URL Shortener

URL shortening service built to learn caching strategies with Redis and FastAPI.

## What It Does

- Create short links with random or custom codes
- Fast redirects using Redis caching
- Click tracking and analytics
- User authentication with JWT
- Link expiration support

## Tech Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL with SQLAlchemy
- Redis for caching
- JWT authentication
- Alembic for migrations

**Infrastructure:**
- Docker for local development
- AWS (EC2, RDS, ElastiCache)
- Terraform for deployment

## Features

**Link Management:**
- Random short code generation
- Custom short codes (with profanity filter)
- Set expiration dates
- Update or delete links

**Analytics:**
- Track clicks with referrer and user agent
- View statistics (total, daily, weekly, monthly)
- Top referrers analysis
- Individual click records

**Caching:**
- Redis cache for fast redirects
- Cache warming on link creation
- Background click tracking (non-blocking)

## What I Learned

### Performance & Caching
- Implementing cache-aside pattern with Redis
- Cache warming vs lazy loading tradeoffs
- When to use background tasks vs inline processing
- Database query optimization with indexes

### System Design
- Building high-read, low-write systems
- Collision handling for random code generation
- Using 302 redirects instead of 301 (for analytics)
- Background task processing with FastAPI

### Infrastructure
- Deploying Redis on AWS ElastiCache
- Setting up RDS PostgreSQL
- Managing infrastructure with Terraform
- Docker containerization

### Key Insights
- **Caching made a big difference:** Redirects went from ~10ms (database) to ~2ms (Redis)
- **Background tasks:** Recording clicks asynchronously keeps redirects fast
- **Cache invalidation is tricky:** Had to think through what happens when links are updated or deleted
- **Random codes vs sequential:** Random is more secure but needs collision handling

## Running Locally

### Prerequisites
- Python 3.12+
- Docker and Docker Compose

### Setup

```bash
# Clone repository
git clone https://github.com/odysian/url-shortener
cd url-shortener

# Start PostgreSQL and Redis
docker-compose up -d

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

## API Endpoints

**Authentication:**
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT token

**Links:**
- `POST /links` - Create short link
- `GET /links` - List your links
- `PATCH /links/{id}` - Update link
- `DELETE /links/{id}` - Delete link

**Redirects:**
- `GET /{short_code}` - Redirect to original URL

**Analytics:**
- `GET /clicks/{link_id}` - View clicks for a link
- `GET /clicks/stats` - Aggregated statistics

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov
```

## Project Structure

```
url-shortener/
├── main.py              # FastAPI app
├── routers/             # API endpoints
│   ├── auth.py          # Registration, login
│   ├── links.py         # Link CRUD
│   └── redirect.py      # Redirects with caching
├── db_models.py         # SQLAlchemy models
├── models.py            # Pydantic schemas
├── auth.py              # JWT utilities
├── redis_config.py      # Redis setup
├── utils/               # Short code generation
├── tests/               # pytest tests
├── alembic/             # Database migrations
└── terraform/           # AWS infrastructure
```

## Deployment

Deployed on AWS using Terraform:
- EC2 for the API
- RDS for PostgreSQL
- ElastiCache for Redis
- GitHub Actions for CI/CD (coming soon)

## Contact

**Chris**
- GitHub: [@odysian](https://github.com/odysian)
- Website: https://odysian.dev
- Email: c.colosimo@odysian.dev

## License

MIT