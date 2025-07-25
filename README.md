# AI Stock Analysis Microservice

A production-ready Python microservice for AI-powered stock and cryptocurrency analysis using FastAPI, yfinance, and OpenAI's GPT-4o-mini.

## Features

- **Multi-Market Support**: US stocks, South African stocks (JSE), and cryptocurrencies
- **Real-time Data**: Integration with yfinance for live market data
- **Technical Analysis**: RSI, SMA, MACD indicators automatically calculated
- **AI-Powered Analysis**: GPT-4o-mini provides BUY/HOLD/SELL recommendations
- **Caching**: Redis caching for optimal performance (12h for data, 24h for analysis)
- **Portfolio Analysis**: Analyze holdings and get rebalancing suggestions
- **Stock Comparison**: Compare multiple assets side-by-side

## Quick Start

### Prerequisites

- Python 3.11+
- Redis (for caching)
- OpenAI API key

### Installation

1. **Clone and setup environment:**

```bash
git clone <repository>
cd trader-agent
cp .env.example .env
```

2. **Configure environment variables in `.env`:**

```env
OPENAI_API_KEY=your-openai-api-key-here
REDIS_URL=redis://localhost:6379
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Run with Docker Compose (recommended):**

```bash
docker-compose up -d
```

Or run locally:

```bash
# Start Redis
redis-server

# Start the API
uvicorn app.main:app --reload
```

5. **Access the API:**

- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## API Endpoints

### Stock Data

#### Get Individual Stock
```http
GET /api/v1/stocks/{symbol}?market=US&period=1mo&interval=1d
```

Example:
```bash
curl "http://localhost:8000/api/v1/stocks/AAPL?market=US"
curl "http://localhost:8000/api/v1/stocks/NPN.JO?market=ZA"
curl "http://localhost:8000/api/v1/stocks/BTC-USD?market=CRYPTO"
```

#### Search Stocks
```http
GET /api/v1/stocks/search?query=apple&market=ALL&limit=10
```

#### Batch Stock Data
```http
POST /api/v1/stocks/batch
Content-Type: application/json

{
  "symbols": ["AAPL", "GOOGL", "BTC-USD"],
  "period": "1mo",
  "interval": "1d"
}
```

### AI Analysis

#### Get Stock Analysis
```http
GET /api/v1/analysis/{symbol}?market=US
```

Returns AI-powered analysis with:
- BUY/HOLD/SELL recommendation
- Confidence score (0-1)
- Target price
- Key analysis points
- Risk assessment

#### Compare Stocks
```http
POST /api/v1/analysis/compare
Content-Type: application/json

{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "metrics": ["performance", "valuation"]
}
```

#### Portfolio Analysis
```http
POST /api/v1/analysis/portfolio
Content-Type: application/json

{
  "holdings": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "purchase_price": 140.00
    }
  ]
}
```

## Symbol Formats

- **US Stocks**: Direct symbol (e.g., `AAPL`, `MSFT`)
- **South African Stocks**: Add `.JO` suffix (e.g., `NPN.JO`, `SHP.JO`)
- **Cryptocurrencies**: Add `-USD` suffix (e.g., `BTC-USD`, `ETH-USD`)

## Configuration

Key environment variables:

```env
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional
REDIS_URL=redis://localhost:6379
API_HOST=0.0.0.0
API_PORT=8000
OPENAI_MODEL=gpt-4o-mini
STOCK_DATA_CACHE_TTL=43200  # 12 hours
ANALYSIS_CACHE_TTL=86400    # 24 hours
LOG_LEVEL=INFO
```

## Performance & Caching

- **Stock Data**: Cached for 12 hours to balance freshness with API efficiency
- **AI Analysis**: Cached for 24 hours as analysis doesn't change frequently
- **Concurrent Operations**: Multiple stocks fetched in parallel
- **Rate Limiting**: Built-in request validation and limiting

## Error Handling

The API provides structured error responses:

```json
{
  "error": {
    "code": "STOCK_NOT_FOUND",
    "message": "The requested stock symbol was not found",
    "details": {
      "symbol": "INVALID",
      "market": "US"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Common error codes:
- `STOCK_NOT_FOUND`: Invalid stock symbol
- `ANALYSIS_FAILED`: AI analysis failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_PARAMETERS`: Invalid request parameters

## Development

### Project Structure

```
app/
├── main.py              # FastAPI application entry
├── config.py            # Configuration settings
├── models/              # Pydantic models
│   ├── stock.py         # Stock data models
│   └── analysis.py      # Analysis models
├── services/            # Business logic
│   ├── stock_service.py     # yfinance integration
│   ├── analysis_service.py  # GPT-4o-mini analysis
│   └── indicator_service.py # Technical indicators
├── routers/             # API endpoints
│   ├── stocks.py        # Stock data routes
│   └── analysis.py      # Analysis routes
└── utils/               # Utilities
    ├── cache.py         # Redis caching
    └── validators.py    # Input validation
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Production Deployment

1. **Environment Setup:**
   - Set `LOG_LEVEL=WARNING` or `ERROR`
   - Configure proper Redis instance
   - Set up monitoring and logging

2. **Docker Production:**
   ```bash
   docker build -t stock-analysis-api .
   docker run -p 8000:8000 --env-file .env stock-analysis-api
   ```

3. **Performance Tuning:**
   - Use Gunicorn with multiple workers
   - Configure Redis persistence
   - Set up load balancing if needed

## Monitoring

Health check endpoints:
- `/health` - Overall API health
- `/api/v1/analysis/health` - Analysis service health

Monitor these metrics:
- Response times
- Cache hit rates
- API call success rates
- OpenAI API usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.