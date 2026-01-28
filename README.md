# Finance Tracker Bot

A sophisticated WhatsApp-powered personal finance tracking system that enables users to log income/expenses and generate financial reports using natural language commands via Twilio's WhatsApp API.

## 🚀 Features

### ✅ Currently Implemented
- **📩 WhatsApp Integration**: Full Twilio webhook support with automatic user creation
- **💬 Natural Language Processing**: Smart parsing of 12+ message patterns with fuzzy matching
- **🧠 Intelligent Categorization**: 40+ predefined categories with auto-suggestions
- **🗂 Persistent Storage**: PostgreSQL with proper relationships and data integrity
- **📊 Financial Reports**: Daily, weekly, monthly, and all-time summaries with visual charts
- **🔄 Conversation State**: Multi-turn dialogs with context persistence
- **💰 Transaction Management**: Full CRUD with amount parsing (decimals, k/m multipliers)
- **📅 Date Processing**: Natural language date parsing (yesterday, last week, etc.)
- **🔍 Search & History**: Transaction history and deletion capabilities
- **📊 Comprehensive Monitoring**: Structured logging, metrics collection, and health checks
- **🛡️ Enhanced Error Handling**: Global error middleware with detailed tracking
- **🔧 Production Ready**: Enterprise-grade logging, monitoring, and configuration

### 🎯 Supported Commands
```bash
# Transaction Logging
"Spent 2500 on food yesterday"
"Income 120000 salary" 
"Paid 800 for transport"
"Bought groceries for 1.5k"

# Reports & Analytics
"Show report"           # All-time summary
"Weekly report"         # Last 7 days
"Monthly summary"       # Last 30 days
"Daily stats"           # Today only

# Management Commands
"Show history"          # Last 10 transactions
"Delete last"           # Remove latest
"Show categories"       # List available categories
"/help"                 # Help documentation
```

## 🛠 Technology Stack

- **Backend Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy 2.0 ORM
- **Messaging**: Twilio WhatsApp API
- **Data Validation**: Pydantic schemas
- **Natural Language**: dateparser + fuzzywuzzy for intelligent parsing
- **Monitoring**: Structured JSON logging with rotation
- **Metrics**: Real-time performance tracking
- **Health Checks**: System resource monitoring
- **Deployment**: Docker with docker-compose support
- **Security**: Twilio signature validation and error tracking

## Project Structure

```
finance-tracker-bot/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── api.py              # API router aggregator
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── webhook.py  # Twilio webhook & testing endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings & configuration
│   │   ├── logging.py          # Logging setup
│   │   └── security.py         # Twilio validation
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy base
│   │   └── session.py          # Database session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User model
│   │   ├── transaction.py      # Transaction model
│   │   └── session.py          # Session model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── webhook.py          # Twilio webhook schema
│   │   └── transaction.py      # Transaction schemas
│   └── services/
│       ├── __init__.py
│       ├── conversation_manager.py # Stateful conversation logic
│       ├── message_processor.py # NLP message parsing
│       ├── finance_engine.py    # Financial calculations & reporting
│       ├── twilio_client.py     # Twilio API wrapper
│       ├── date_parser.py       # Natural language date processing
│       └── report_formatter.py  # WhatsApp-optimized formatting
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 18
- Twilio Account with WhatsApp Sandbox

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Twilio credentials and database settings
   ```

5. Create the database:
   ```sql
   CREATE DATABASE financetracker;
   ```

6. Create database tables:
    ```bash
    # In the project directory, run:
    python -c "
from app.db.base import Base
from app.models import user, transaction, session
from app.db.session import engine
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
    ```

7. Run the application:
    ```bash
    uvicorn app.main:app --reload
    ```

## 📱 Usage Guide

### Transaction Logging

Send natural language messages to your WhatsApp bot:

```bash
# Basic expenses
"Spent 2500 on food"
"Paid 800 for transport"
"Bought groceries for 1500"

# Income tracking  
"Income 120000 salary"
"Received 1000 bonus"

# With dates and multipliers
"Spent 2.5k on rent yesterday"
"Paid 500 for internet last week"
"Income 1.2m salary this month"
```

### Reports & Analytics

```bash
"Show report"           # All-time summary
"Weekly report"         # Last 7 days  
"Monthly summary"       # Last 30 days
"Daily stats"           # Today only
```

### Management Commands

```bash
"Show history"          # Last 10 transactions
"Delete last"           # Remove latest transaction
"Show categories"       # List all available categories
"/help"                 # Help documentation
```

### Smart Features

- **Auto-categorization**: Recognizes 40+ categories with fuzzy matching
- **Date parsing**: Understands "yesterday", "last week", "Jan 15", etc.
- **Amount multipliers**: Supports "k" (thousand) and "m" (million)
- **Conversation memory**: Remembers context during multi-step interactions

## 🌐 API Endpoints

### Production
- `POST /api/v1/webhook` - Twilio WhatsApp webhook (main endpoint)

### Development & Testing  
- `POST /api/v1/verify/message` - Direct message testing (bypasses Twilio)
- `GET /` - Application information and status

### Monitoring & Health
- `GET /monitoring/health` - System health check with monitoring
- `GET /monitoring/metrics` - Application metrics and performance data
- `POST /monitoring/metrics/reset` - Reset application metrics

### Documentation
- `GET /docs` - Interactive API documentation (Swagger)
- `GET /redoc` - API documentation (ReDoc)

## 🧪 Testing

```bash
# Test message processing directly
curl -X POST http://localhost:8000/api/v1/verify/message \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "message=Spent 2500 on food&phone=+1234567890"

# Test health check
curl http://localhost:8000/monitoring/health

# Test metrics collection
curl http://localhost:8000/monitoring/metrics
```

## 📊 Database Schema

```sql
users (phone_number PK, created_at)
├── transactions (id PK, user_phone FK, amount, category, type, description, 
                  transaction_date, timestamp, updated_at)
└── sessions (user_phone FK, state, context JSON, last_interaction)
```

## 🔧 Development Architecture

The application follows clean architecture principles:
- **Service Layer**: Business logic separated from API layer
- **Repository Pattern**: Database access abstracted through models  
- **Dependency Injection**: FastAPI's DI for database sessions
- **Schema Validation**: Pydantic ensures data integrity
- **Error Handling**: Comprehensive middleware with detailed logging
- **Monitoring**: Request tracking, metrics collection, and health monitoring
- **Configuration**: Environment-aware settings with extensive customization

## 📊 Monitoring & Logging

### Logging Features
- **Structured JSON logs** with timestamps and context
- **Log rotation** (10MB files, 5 backups)  
- **Request ID tracking** for end-to-end tracing
- **Database query logging** with performance timing
- **Error tracking** with stack traces and context

### Health Monitoring
- **System metrics**: CPU, memory, disk usage
- **Database health**: Connection status and performance
- **Application metrics**: Request rates, response times, error rates
- **Real-time alerts**: Configurable thresholds and notifications

### Configuration
```env
# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_REQUEST_BODY=false
ENABLE_STRUCTURED_LOGGING=true

# Monitoring Configuration  
ENABLE_METRICS=true
ENABLE_HEALTH_CHECKS=true
METRICS_RETENTION_HOURS=24

# Performance Tuning
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
REQUEST_TIMEOUT_SECONDS=60
```

## 🚀 Production Readiness

### ✅ Production Ready
- Core transaction logging and reporting
- WhatsApp integration with Twilio
- Database persistence and relationships
- Container deployment (Docker)
- Comprehensive monitoring and logging
- Enhanced error handling and security
- Structured metrics collection
- Health check endpoints

## 📈 Planned Features

- **Budget tracking & alerts**: Set spending limits and receive notifications
- **Recurring transactions**: Automated monthly/weekly expense tracking
- **Data export**: CSV/PDF reports for external analysis
- **Advanced analytics**: Spending trends, category insights, and forecasting
- **Multi-currency support**: Handle transactions in different currencies
- **Web dashboard**: Visual interface for managing finances
- **Bank integration**: Direct transaction import from banking APIs
- **Goal tracking**: Savings goals and progress monitoring
- **Team/family accounts**: Shared expense tracking for groups

## 📝 License

MIT License - see LICENSE file for details
