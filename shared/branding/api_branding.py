"""
Branding API Endpoints
Manage company branding (logo, name, colors)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from pathlib import Path
import shutil

from shared.branding.company_branding import CompanyBrandingManager
from shared.config.logging_config import get_logger


logger = get_logger(__name__)

# Create router
branding_router = APIRouter(prefix="/branding", tags=["branding"])

# Initialize branding manager
branding_manager = CompanyBrandingManager()


@branding_router.post("/setup")
async def setup_branding(
    user_id: str = Form(...),
    company_name: str = Form(...),
    logo: Optional[UploadFile] = File(None),
    primary_color: Optional[str] = Form(None),
    secondary_color: Optional[str] = Form(None),
    accent_color: Optional[str] = Form(None)
):
    """
    Setup company branding
    
    Args:
        user_id: User/company identifier
        company_name: Company name
        logo: Company logo image (optional)
        primary_color: Primary brand color hex (optional, auto-generated if not provided)
        secondary_color: Secondary color hex (optional)
        accent_color: Accent color hex (optional)
        
    Returns:
        Branding configuration
    """
    try:
        # Save logo if provided
        logo_path = None
        if logo:
            # Save uploaded logo
            logo_dir = Path("./data/branding/temp")
            logo_dir.mkdir(parents=True, exist_ok=True)
            
            logo_path = logo_dir / logo.filename
            with open(logo_path, "wb") as f:
                shutil.copyfileobj(logo.file, f)
        
        # Create branding
        branding = branding_manager.create_branding(
            user_id=user_id,
            company_name=company_name,
            logo_path=str(logo_path) if logo_path else None,
            primary_color=primary_color,
            secondary_color=secondary_color,
            accent_color=accent_color
        )
        
        # Clean up temp logo
        if logo_path and logo_path.exists():
            logo_path.unlink()
        
        return {
            "status": "success",
            "message": f"Branding created for {company_name}",
            "branding": branding
        }
        
    except Exception as e:
        logger.error(f"Failed to setup branding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@branding_router.put("/update/{user_id}")
async def update_branding(
    user_id: str,
    company_name: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    primary_color: Optional[str] = Form(None),
    secondary_color: Optional[str] = Form(None),
    accent_color: Optional[str] = Form(None)
):
    """Update existing branding"""
    try:
        # Save logo if provided
        logo_path = None
        if logo:
            logo_dir = Path("./data/branding/temp")
            logo_dir.mkdir(parents=True, exist_ok=True)
            
            logo_path = logo_dir / logo.filename
            with open(logo_path, "wb") as f:
                shutil.copyfileobj(logo.file, f)
        
        # Update branding
        branding = branding_manager.update_branding(
            user_id=user_id,
            company_name=company_name,
            logo_path=str(logo_path) if logo_path else None,
            primary_color=primary_color,
            secondary_color=secondary_color,
            accent_color=accent_color
        )
        
        # Clean up
        if logo_path and logo_path.exists():
            logo_path.unlink()
        
        return {
            "status": "success",
            "message": "Branding updated",
            "branding": branding
        }
        
    except Exception as e:
        logger.error(f"Failed to update branding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@branding_router.get("/{user_id}")
async def get_branding(user_id: str):
    """Get branding for user"""
    try:
        branding = branding_manager.get_branding(user_id)
        
        if not branding:
            raise HTTPException(status_code=404, detail=f"No branding found for user: {user_id}")
        
        return branding
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get branding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@branding_router.get("/")
async def list_brandings():
    """List all configured brandings"""
    try:
        brandings = branding_manager.list_brandings()
        return {
            "total": len(brandings),
            "brandings": brandings
        }
        
    except Exception as e:
        logger.error(f"Failed to list brandings: {e}")
        raise HTTPException(status_code=500, detail=str(e))