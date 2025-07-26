# CLAUDE.md - AI Stock Analysis Microservice

## Project Overview

This microservice provides a RESTful API for fetching stock data and AI-powered analysis for US stocks, South African (JSE) stocks, and cryptocurrencies. The system uses FastAPI for the web framework, yfinance for real-time market data, and OpenAI's GPT-4o-mini for intelligent analysis with structured outputs.

## Architecture

### Core Technology Stack

1. **FastAPI** - Modern web framework with automatic OpenAPI documentation
2. **OpenAI GPT-4o-mini** - AI analysis with structured output parsing
3. **yfinance** - Real-time stock and cryptocurrency data
4. **Redis** - Caching layer for performance optimization
5. **Pydantic** - Data validation and settings management
6. **Docker** - Containerization and orchestration

### System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Test Frontend │    │   FastAPI App    │    │   OpenAI API    │
│   (HTML/JS)     │◄──►│                  │◄──►│   GPT-4o-mini   │
└─────────────────┘    │  - Routers       │    └─────────────────┘
                       │  - Services      │
┌─────────────────┐    │  - Models        │    ┌─────────────────┐
│     Redis       │◄──►│  - Validators    │◄──►│   yfinance      │
│    (Cache)      │    │                  │    │   (Market Data) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Directory Structure

```
trader-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings using Pydantic
│   ├── models/              # Pydantic models for data validation
│   │   ├── __init__.py
│   │   ├── stock.py         # Stock data models
│   │   └── analysis.py      # Analysis response models
│   ├── services/            # Business logic layer
│   │   ├── __init__.py
│   │   ├── stock_service.py     # Stock data fetching via yfinance
│   │   ├── analysis_service.py  # OpenAI GPT-4o-mini integration
│   │   └── indicator_service.py # Technical indicators calculation
│   ├── routers/             # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── stocks.py        # Stock data endpoints
│   │   └── analysis.py      # AI analysis endpoints
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── cache.py         # Redis caching utilities
│       └── validators.py    # Input validation helpers
├── frontend/
│   ├── index.html           # Test interface for API testing
│   └── README.md           # Frontend documentation
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-container orchestration
├── README.md               # User documentation
└── CLAUDE.md               # Technical documentation (this file)
```

## API Design

### Stock Data Endpoints

#### 1. Individual Stock Data
```http
GET /api/v1/stocks/{symbol}
Query Parameters:
  - market: "US" | "ZA" | "CRYPTO" (default: "US")
  - period: "1d" | "5d" | "1mo" | "3mo" | "6mo" | "1y" | "2y" | "5y" | "10y" | "ytd" | "max"
  - interval: "1m" | "2m" | "5m" | "15m" | "30m" | "60m" | "90m" | "1h" | "1d" | "5d" | "1wk" | "1mo" | "3mo"

Response:
{
  "symbol": "AAPL",
  "market": "US",
  "company_name": "Apple Inc.",
  "current_price": 150.25,
  "currency": "USD",
  "change_percent": 2.1,
  "volume": 75000000,
  "market_cap": 2500000000000,
  "pe_ratio": 25.5,
  "dividend_yield": 0.5,
  "historical_data": [...],
  "technical_indicators": {
    "rsi": 45.2,
    "sma_20": 148.5,
    "sma_50": 145.8,
    "macd": {...}
  }
}
```

#### 2. Stock Search
```http
GET /api/v1/stocks/search
Query Parameters:
  - query: string (company name or ticker)
  - market: "US" | "ZA" | "CRYPTO" | "ALL"
  - limit: integer (default: 10, max: 50)

Response:
{
  "results": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "market": "US",
      "sector": "Technology",
      "current_price": 150.25
    }
  ],
  "total_found": 25,
  "query": "apple"
}
```

#### 3. Batch Stock Data
```http
POST /api/v1/stocks/batch
Content-Type: application/json

{
  "symbols": ["AAPL", "GOOGL", "BTC-USD"],
  "period": "1mo",
  "interval": "1d"
}

Response:
{
  "stocks": [...],
  "successful": 3,
  "failed": 0,
  "errors": []
}
```

### AI Analysis Endpoints

#### 1. Stock Analysis with GPT-4o-mini
```http
GET /api/v1/analysis/{symbol}
Query Parameters:
  - market: "US" | "ZA" | "CRYPTO"

Response:
{
  "symbol": "AAPL",
  "timestamp": "2024-01-15T10:30:00Z",
  "recommendation": "BUY" | "HOLD" | "SELL",
  "confidence_score": 0.85,
  "target_price": 165.50,
  "reasoning": [
    "Strong quarterly earnings growth exceeding expectations",
    "Positive technical indicators with RSI at healthy levels",
    "Market leadership position in AI and services expansion"
  ],
  "key_points": [
    "Revenue growth of 8% YoY driven by services segment",
    "iPhone sales stabilizing in key markets",
    "Strong cash position enabling continued innovation"
  ],
  "risks": [
    "Regulatory pressure in EU markets",
    "Supply chain dependencies in Asia",
    "Market saturation in smartphone segment"
  ],
  "technical_analysis": {
    "rsi": 45.2,
    "rsi_signal": "neutral",
    "sma_20": 150.25,
    "sma_50": 148.80,
    "sma_200": 145.60,
    "macd_signal": "bullish",
    "price_vs_sma20": "above",
    "trend": "upward"
  },
  "market_context": "Technology sector showing strength amid AI optimism"
}
```

#### 2. Stock Comparison
```http
POST /api/v1/analysis/compare
Content-Type: application/json

{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "metrics": ["performance", "valuation", "growth"]
}

Response:
{
  "comparison": {
    "performance": {...},
    "valuation": {...},
    "growth": {...}
  },
  "recommendation": "AAPL",
  "reasoning": [
    "Strongest technical momentum",
    "Superior profit margins",
    "Best risk-adjusted returns"
  ],
  "ranking": ["AAPL", "MSFT", "GOOGL"]
}
```

#### 3. Portfolio Analysis
```http
POST /api/v1/analysis/portfolio
Content-Type: application/json

{
  "holdings": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "purchase_price": 140.00
    },
    {
      "symbol": "MSFT",
      "quantity": 50,
      "purchase_price": 300.00
    }
  ]
}

Response:
{
  "total_value": 30025.00,
  "total_cost": 29000.00,
  "total_gain_loss": 1025.00,
  "total_gain_loss_percent": 3.53,
  "holdings_analysis": [...],
  "recommendations": [
    "Consider taking profits on AAPL position",
    "MSFT showing strong momentum for continued holding"
  ],
  "rebalancing_suggestions": [
    "Reduce AAPL allocation to 40%",
    "Maintain MSFT at current 50%",
    "Consider adding defensive position"
  ],
  "risk_assessment": "Moderate - concentrated in technology sector"
}
```

### Monitoring & Health Endpoints

#### 1. Application Health
```http
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "dependencies": {
    "redis": "connected",
    "yfinance": "available"
  }
}
```

#### 2. Analysis Service Health
```http
GET /api/v1/analysis/health

Response:
{
  "status": "healthy",
  "service": "analysis",
  "openai_configured": true,
  "cache_available": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 3. Token Usage Statistics
```http
GET /api/v1/analysis/tokens

Response:
{
  "status": "success",
  "token_usage": {
    "total_tokens_used": 15420,
    "total_estimated_cost": 0.0234,
    "session_start": "2024-01-15T09:00:00Z",
    "operations_count": 12,
    "average_tokens_per_operation": 1285
  }
}
```

## AI Integration with OpenAI

### GPT-4o-mini Implementation

The system uses OpenAI's GPT-4o-mini with structured output parsing for consistent, reliable analysis results.

#### Key Features:
- **Structured Output**: Uses Pydantic models for guaranteed response format
- **Cost Tracking**: Monitors token usage and estimated costs
- **Error Handling**: Graceful fallbacks for API failures
- **Caching**: 24-hour cache for analysis results

#### Analysis Process:
1. **Data Gathering**: Fetch current stock data and technical indicators
2. **Context Building**: Create comprehensive prompt with market data
3. **AI Analysis**: Send structured request to GPT-4o-mini
4. **Response Parsing**: Validate and parse structured output
5. **Caching**: Store results for 24-hour reuse

#### Prompt Engineering:

The system uses market-specific prompts optimized for different asset types:

```python
# US Market Prompt
"""You are an expert financial analyst specializing in US equity markets. 
Analyze the provided stock data and give a comprehensive investment recommendation.
Consider technical indicators, fundamental metrics, market context, and current trends."""

# South African Market Prompt  
"""You are an expert financial analyst specializing in the Johannesburg Stock Exchange (JSE).
Analyze the provided South African stock data considering local market dynamics,
currency effects, and regional economic factors."""

# Cryptocurrency Prompt
"""You are an expert cryptocurrency analyst. Analyze the provided crypto asset data
considering blockchain fundamentals, market sentiment, regulatory environment,
and technical analysis specific to digital assets."""
```

### Technical Indicators Integration

The system calculates and includes technical indicators in AI analysis:

- **RSI (Relative Strength Index)**: Momentum oscillator (0-100)
- **SMA (Simple Moving Averages)**: 20, 50, and 200-day averages  
- **MACD**: Moving Average Convergence Divergence
- **Price Position**: Relative to key moving averages
- **Trend Analysis**: Overall price trend direction

## Data Models

### Core Pydantic Models

#### Stock Data Model
```python
class StockData(BaseModel):
    symbol: str
    market: Literal["US", "ZA", "CRYPTO"]
    company_name: str
    current_price: float
    currency: str
    change_percent: float
    volume: int
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    technical_indicators: TechnicalIndicators
    historical_data: List[HistoricalDataPoint]
```

#### Analysis Output Model
```python
class StockAnalysisOutput(BaseModel):
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    target_price: Optional[float]
    reasoning: List[str]
    key_points: List[str]
    risks: List[str]
    market_context: str
```

#### Technical Indicators Model
```python
class TechnicalIndicators(BaseModel):
    rsi: float
    rsi_signal: Literal["oversold", "neutral", "overbought"]
    sma_20: float
    sma_50: float
    sma_200: Optional[float]
    macd_signal: Literal["bullish", "bearish", "neutral"]
    price_vs_sma20: Literal["above", "below", "at"]
    trend: Literal["upward", "downward", "sideways"]
```

## Configuration Management

### Environment Variables
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# OpenAI Configuration
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-4o-mini

# Redis Configuration
REDIS_URL=redis://localhost:6379
STOCK_DATA_CACHE_TTL=43200    # 12 hours
ANALYSIS_CACHE_TTL=86400      # 24 hours

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Market Data Configuration
YFINANCE_TIMEOUT=30
```

### Settings Management

The configuration uses Pydantic Settings for type-safe environment variable handling:

```python
class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # Redis Configuration  
    redis_url: str = "redis://localhost:6379"
    stock_data_cache_ttl: int = 43200  # 12 hours
    analysis_cache_ttl: int = 86400    # 24 hours
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
```

## Caching Strategy

### Redis Implementation

The system uses Redis for intelligent caching with different TTL values:

#### Cache Keys:
- Stock Data: `stock:{symbol}:{market}:{period}:{interval}`
- Analysis: `analysis:{symbol}:{market}`
- Search Results: `search:{query}:{market}:{limit}`

#### Cache TTL:
- **Stock Data**: 12 hours (43,200 seconds)
- **Analysis Results**: 24 hours (86,400 seconds)
- **Search Results**: 1 hour (3,600 seconds)

#### Cache Management:
```python
class CacheManager:
    async def get_stock_data(self, key: str) -> Optional[dict]:
        """Retrieve cached stock data"""
        
    async def set_stock_data(self, key: str, data: dict, ttl: int = None):
        """Cache stock data with TTL"""
        
    async def get_analysis(self, key: str) -> Optional[dict]:
        """Retrieve cached analysis"""
        
    async def set_analysis(self, key: str, analysis: dict, ttl: int = None):
        """Cache analysis with TTL"""
```

## Error Handling & Validation

### Structured Error Responses

All errors return consistent JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "additional_context"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "uuid-string"
}
```

### Error Categories

#### Stock Data Errors:
- `STOCK_NOT_FOUND`: Invalid or delisted stock symbol
- `MARKET_DATA_UNAVAILABLE`: yfinance service unavailable
- `INVALID_SYMBOL_FORMAT`: Malformed stock symbol

#### Analysis Errors:
- `ANALYSIS_FAILED`: OpenAI API error or parsing failure
- `INSUFFICIENT_DATA`: Not enough data for analysis
- `OPENAI_RATE_LIMIT`: OpenAI API rate limit exceeded

#### System Errors:
- `CACHE_UNAVAILABLE`: Redis connection issues
- `RATE_LIMIT_EXCEEDED`: API rate limiting triggered
- `INVALID_PARAMETERS`: Request validation failures

### Input Validation

Comprehensive validation using Pydantic:

```python
class StockSymbolValidator:
    @staticmethod
    def validate_symbol(symbol: str, market: str) -> str:
        """Validate and normalize stock symbols"""
        
    @staticmethod  
    def validate_market(market: str) -> str:
        """Validate market parameter"""
        
    @staticmethod
    def validate_period(period: str) -> str:
        """Validate time period parameter"""
```

## Performance Optimization

### Async Implementation

All I/O operations use asyncio for optimal performance:
- HTTP requests to external APIs
- Redis cache operations
- Database queries (if implemented)
- OpenAI API calls

### Concurrent Processing

Batch operations process multiple stocks in parallel:
```python
async def fetch_multiple_stocks(symbols: List[str]) -> List[StockData]:
    tasks = [fetch_single_stock(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

### Connection Pooling

- Redis connection pool for cache operations
- HTTP session reuse for external API calls
- OpenAI client with connection pooling

## Security Considerations

### API Security

1. **Input Sanitization**: All inputs validated and sanitized
2. **Rate Limiting**: Per-IP and per-API-key limits
3. **CORS Configuration**: Configurable origin restrictions
4. **Request Size Limits**: Maximum payload size enforcement

### Production Security

1. **Environment Variables**: Sensitive data in environment variables
2. **Container Security**: Non-root user in Docker containers
3. **Health Checks**: Monitoring endpoints for system health
4. **Logging**: Structured logging without sensitive data

## Testing Strategy

### Unit Tests
- Service layer testing with mocked dependencies
- Model validation testing
- Utility function testing

### Integration Tests
- API endpoint testing
- Cache integration testing
- External service integration testing

### Performance Tests
- Load testing with realistic traffic patterns
- Cache performance validation
- OpenAI API rate limit testing

## Deployment Architecture

### Docker Configuration

#### Multi-stage Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### Production Deployment

#### Recommended Infrastructure:
- **Container Orchestration**: Docker Compose or Kubernetes
- **Load Balancer**: Nginx or cloud load balancer
- **Cache**: Managed Redis instance
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK stack or cloud logging

#### Environment Configuration:
```env
# Production settings
LOG_LEVEL=WARNING
API_HOST=0.0.0.0
API_PORT=8000

# External services
REDIS_URL=redis://production-redis:6379
OPENAI_API_KEY=production-key

# Performance tuning
STOCK_DATA_CACHE_TTL=43200
ANALYSIS_CACHE_TTL=86400
RATE_LIMIT_PER_MINUTE=100
```

## Monitoring & Observability

### Health Monitoring

- Application health endpoints
- Service dependency checks
- Performance metrics collection

### Business Metrics

- API request volumes and patterns
- Analysis accuracy and user feedback
- Token usage and cost tracking
- Popular stock symbols and markets

### System Metrics

- Response time percentiles
- Error rates by endpoint
- Cache hit/miss ratios
- Resource utilization (CPU, memory)

### Alerting

- High error rates
- Slow response times
- External service failures
- OpenAI API quota warnings

## Future Enhancements

### Potential Improvements

1. **Real-time Data**: WebSocket connections for live price updates
2. **Advanced Analytics**: More sophisticated technical analysis
3. **User Management**: Authentication and personalized portfolios
4. **Historical Analysis**: Backtesting and historical performance analysis
5. **Alternative Data**: Sentiment analysis, news integration
6. **Multi-language Support**: Localization for different markets

### Scalability Considerations

1. **Microservices**: Split into specialized services
2. **Message Queues**: Async processing for heavy operations
3. **Database Integration**: Persistent storage for user data
4. **CDN Integration**: Static asset delivery optimization
5. **Multi-region Deployment**: Global latency optimization

This technical documentation provides a comprehensive overview of the AI Stock Analysis Microservice architecture, implementation details, and operational considerations. The system is designed for production use with emphasis on performance, reliability, and maintainability.
