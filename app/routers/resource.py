from fastapi import File, UploadFile, Form, Depends, HTTPException, APIRouter
from app.database import get_db
import os
import httpx
import PyPDF2

resource_router = APIRouter()
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@resource_router.post("/add-resource")
async def add_resource(
    user_id: int = Form(...),
    subject_id: int = Form(None),
    title: str = Form(...),
    source_type: str = Form(...),
    url: str = Form(None),
    note_text: str = Form(None),
    file: UploadFile = File(None),
    db=Depends(get_db),
):
    raw_text = None
    file_path = None

    try:
        if source_type == "pdf":
            if not file:
                raise HTTPException(status_code=400, detail="PDF file required")

            # os.path.basename prevents path traversal (e.g. ../../app/main.py)
            safe_name = os.path.basename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, safe_name)
            with open(file_path, "wb") as f:
                f.write(await file.read())

            raw_text = ""
            with open(file_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                for page in reader.pages:
                    raw_text += page.extract_text() or ""

        elif source_type == "url":
            if not url:
                raise HTTPException(status_code=400, detail="URL required")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                response.raise_for_status()
            raw_text = response.text

        elif source_type == "note":
            if not note_text:
                raise HTTPException(status_code=400, detail="Note text required")
            raw_text = note_text

        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")

        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO studyguide.resources
                (user_id, subject_id, title, source_type, file_path, url, raw_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING resource_id
            """,
            (user_id, subject_id, title, source_type, file_path, url, raw_text),
        )
        resource_id = cur.fetchone()[0]
        db.commit()
        cur.close()

        return {
            "resource_id": resource_id,
            "title": title,
            "source_type": source_type,
            "message": "Resource added successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
