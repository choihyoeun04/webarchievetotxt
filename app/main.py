from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import io
from app.parser import parse_webarchive
from app.config import MAX_FILE_SIZE, VERSION

app = FastAPI(title="WebArchive to Text Converter", version=VERSION)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve upload interface."""
    with open("app/static/index.html", "r") as f:
        return f.read()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": VERSION}


@app.post("/api/convert")
async def convert(file: UploadFile = File(...)):
    """Convert .webarchive file to plain text."""
    if not file:
        raise HTTPException(status_code=422, detail="Missing file in request")
    
    # Read file
    file_bytes = await file.read()
    
    # Check file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (>50MB)")
    
    # Parse and convert
    try:
        text = parse_webarchive(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server processing error")
    
    # Return as downloadable text file
    text_bytes = text.encode('utf-8')
    return StreamingResponse(
        io.BytesIO(text_bytes),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=\"converted.txt\""
        }
    )
