from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import io
from typing import List
from app.parser import parse_webarchive
from app.config import MAX_FILE_SIZE, VERSION

app = FastAPI(title="WebArchive to Text Converter", version=VERSION)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve upload interface."""
    with open("app/static/index.html", "r") as f:
        return f.read()


@app.get("/robots.txt")
async def robots():
    """Serve robots.txt for SEO."""
    return FileResponse("app/static/robots.txt", media_type="text/plain")


@app.get("/sitemap.xml")
async def sitemap():
    """Serve sitemap.xml for SEO."""
    return FileResponse("app/static/sitemap.xml", media_type="application/xml")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": VERSION}


@app.post("/api/convert")
async def convert(file: UploadFile = File(...)):
    """Convert .webarchive file to plain text."""
    if not file:
        raise HTTPException(status_code=422, detail="Missing file in request")
    
    file_bytes = await file.read()
    
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (>50MB)")
    
    try:
        text = parse_webarchive(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server processing error")
    
    original_name = file.filename or "converted"
    output_name = original_name[:-11] + '.txt' if original_name.endswith('.webarchive') else original_name + '.txt'
    
    text_bytes = text.encode('utf-8')
    return StreamingResponse(
        io.BytesIO(text_bytes),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{output_name}\""}
    )


@app.post("/api/convert-batch")
async def convert_batch(files: List[UploadFile] = File(...)):
    """Convert multiple .webarchive files and return results as JSON."""
    if not files:
        raise HTTPException(status_code=422, detail="No files provided")
    
    results = []
    for file in files:
        file_bytes = await file.read()
        
        if len(file_bytes) > MAX_FILE_SIZE:
            results.append({"filename": file.filename, "error": "File too large (>50MB)"})
            continue
        
        try:
            text = parse_webarchive(file_bytes)
            original_name = file.filename or "converted"
            output_name = original_name[:-11] + '.txt' if original_name.endswith('.webarchive') else original_name + '.txt'
            results.append({"filename": output_name, "text": text})
        except ValueError as e:
            results.append({"filename": file.filename, "error": str(e)})
        except Exception:
            results.append({"filename": file.filename, "error": "Processing error"})
    
    return JSONResponse(content={"results": results})



