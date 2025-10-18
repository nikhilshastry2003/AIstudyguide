# upload resources
from fastapi import File, UploadFile, Form , Depends
from app.database import get_db
import psycopg2
import os
import requests
import PyPDF2
from fastapi import FastAPI, HTTPException, APIRouter
from app.schemas import UserCreate , UserLogin
from passlib.context import CryptContext


resource_router = APIRouter()
# Folder where we’ll store uploaded PDFs
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@resource_router.post("/add-resource")
async def add_resource(
    user_id: int = Form(...),  # who is uploading the resource
    subject_id: int = Form(None),  # optional subject link
    title: str = Form(...),  # resource title
    source_type: str = Form(...),  # pdf / url / note
    url: str = Form(None),  # only used if source_type = url
    note_text: str = Form(None),  # only used if source_type = note
    file: UploadFile = File(None),  # only used if source_type = pdf
db=Depends(get_db)):
    """
    Add a new resource to the database.
    Steps:
    1. Handle different source types (pdf, url, note).
    2. Extract raw_text if possible.
    3. Save entry in studyguide.resources.
    """
    raw_text = None
    file_path = None

    try:
        # Case 1: Handle PDF upload
        if source_type == "pdf":
            if not file:
                raise HTTPException(status_code=400, detail="PDF file required")

            # Save file to uploads folder
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())

            # Extract text from PDF
            raw_text = ""
            with open(file_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                for page in reader.pages:
                    raw_text += page.extract_text() or ""

        # Case 2: Handle URL
        elif source_type == "url":
            if not url:
                raise HTTPException(status_code=400, detail="URL required")
            response = requests.get(url)
            raw_text = response.text

        # Case 3: Handle Note
        elif source_type == "note":
            if not note_text:
                raise HTTPException(status_code=400, detail="Note text required")
            raw_text = note_text

        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")

        # Save into DB
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO studyguide.resources 
                (user_id, subject_id, title, source_type, file_path, url, raw_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING resource_id
            """,
            (user_id, subject_id, title, source_type, file_path, url, raw_text)
        )
        resource_id = cur.fetchone()[0]
        db.commit()
        cur.close()

        return {
            "resource_id": resource_id,
            "title": title,
            "source_type": source_type,
            "message": "Resource added successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    