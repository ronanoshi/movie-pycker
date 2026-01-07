# Movie Pycker

A FastAPI-based backend service for indexing and searching local movie libraries.

## Features

- 🎬 Index local video files (`.mp4`, `.mkv`, `.avi`)
- 📊 Extract technical metadata (duration) using pymediainfo
- 🌐 Enrich movies with OMDb API (genres, plot, etc.)
- 🔍 Search movies by keywords with flexible sorting
- ⚡ Fast async API built with FastAPI

## Requirements

- Python 3.11+
- OMDb API key (free tier: [http://www.omdbapi.com/apikey.aspx](http://www.omdbapi.com/apikey.aspx))

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd movie-pycker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```env
MOVIE_DIRECTORY=/path/to/your/movies
OMDB_API_KEY=your_api_key_here
AUTO_INDEX_ON_STARTUP=true
```

## Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

## API Endpoints

### GET /movies
List all indexed movies with optional sorting.

**Query Parameters:**
- `sort` (optional): Sort field (`duration` or `-duration` for descending)

**Example:**
```bash
curl http://localhost:8000/movies?sort=-duration
```

### POST /movies/search
Search movies by keywords with filtering and sorting.

**Request Body:**
```json
{
  "keywords": ["thriller", "dark"],
  "sort": "-duration"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/movies/search \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["thriller"], "sort": "duration"}'
```

### POST /movies/rescan
Trigger re-indexing of the movie directory.

**Example:**
```bash
curl -X POST http://localhost:8000/movies/rescan
```

### GET /health
Health check endpoint.

## Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_search.py -v
```

## Project Structure

```
app/
├── main.py                    # FastAPI app initialization
├── api/
│   └── movies.py             # API endpoints
├── services/
│   ├── indexer.py            # Directory scanning & metadata extraction
│   ├── metadata_enrichment.py # OMDb enrichment
│   └── search.py             # Search logic
├── domain/
│   └── movie.py              # Domain models (Pydantic)
├── infrastructure/
│   ├── omdb_client.py        # OMDb API client
│   ├── media_info.py         # Media metadata extraction interface
│   └── cache.py              # Cache interface & implementation
└── core/
    └── config.py             # Configuration management
tests/
├── conftest.py               # Test fixtures
├── test_*.py                 # Test modules
└── test_integration.py       # Integration tests
```

## Development

This project follows Python best practices:
- PEP 8 code style
- Type hints throughout
- Comprehensive testing
- Clean architecture with separation of concerns

## License

MIT

