from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import io

from app.database import get_db
from app.models.models import User, File
from app.schemas.schemas import FileResponse
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/files", tags=["Files"])

@router.post("/", response_model=FileResponse)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file
    """
    # Read file content
    content = await file.read()
    
    # Check file size (max 50KB)
    if len(content) > 50 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50KB limit")
    
    # Create new file
    db_file = File(
        filename=file.filename,
        content_type=file.content_type,
        size=len(content),
        data=content
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file

@router.get("/", response_model=List[FileResponse])
async def read_files(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of files
    """
    files = db.query(File).offset(skip).limit(limit).all()
    return files

@router.get("/{file_id}", response_model=FileResponse)
async def read_file_info(
    file_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get file information
    """
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    return db_file

@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download a file
    """
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    return Response(
        content=db_file.data,
        media_type=db_file.content_type,
        headers={"Content-Disposition": f"attachment; filename={db_file.filename}"}
    )

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a file
    """
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    db.delete(db_file)
    db.commit()
    
    return None