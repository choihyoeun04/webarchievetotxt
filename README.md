# WebArchive to Text Converter

A simple web application to convert iOS .webarchive files to plain text.

## Features

- Upload .webarchive files via drag-and-drop or file picker
- Extracts clean, readable text with proper paragraph separation
- Downloads result as UTF-8 .txt file
- Handles files up to 50MB
- No database required - stateless processing

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn app.main:app --reload
```

3. Open browser to http://localhost:8000

### Docker Deployment

1. Build image:
```bash
docker build -t webarchive-converter .
```

2. Run container:
```bash
docker run -p 8000:8000 webarchive-converter
```

3. Access at http://localhost:8000

## API Endpoints

### POST /api/convert
Upload .webarchive file and receive plain text.

**Request:** multipart/form-data with `file` field

**Response:** text/plain file download

**Errors:**
- 400: Invalid file format
- 413: File too large (>50MB)
- 422: Missing file
- 500: Processing error

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Technical Details

- **Backend:** Python + FastAPI
- **HTML Parsing:** BeautifulSoup4
- **File Format:** Apple binary plist with base64-encoded HTML
- **Max File Size:** 50MB
- **Processing Timeout:** 30 seconds

## License

MIT
