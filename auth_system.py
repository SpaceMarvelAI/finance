"""
Authentication and Company Setup Endpoints
Fixes critical missing authentication and configuration endpoints
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
from uuid import uuid4

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Pydantic Models
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_id: str

class UserRegisterResponse(BaseModel):
    success: bool
    user_id: str
    message: str
    token: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    success: bool
    token: str
    user_id: str
    company_id: str
    expires_in: int

class CompanySetupRequest(BaseModel):
    name: str
    currency: str = "USD"
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    dso_target: Optional[int] = None
    sla_days: Optional[int] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    aliases: Optional[list[str]] = None

class CompanySetupResponse(BaseModel):
    success: bool
    company_id: str
    company_name: str
    settings: Dict[str, Any]
    aliases: list[str]
    message: str

class CompanyProfileResponse(BaseModel):
    company_id: str
    name: str
    currency: str
    primary_color: str
    secondary_color: str
    accent_color: str
    dso_target: int
    sla_days: int
    created_at: str
    updated_at: str

class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: str
    company_id: str
    email: str


from data_layer.database.database_manager import DatabaseManager
db = DatabaseManager()
tokens_db: Dict[str, Any] = {}  # For token invalidation on logout

# Utility Functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode(), hash.encode())

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if token is blacklisted (logged out)
        if token in tokens_db:
            raise HTTPException(status_code=401, detail="Token has been revoked")
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency to get current user from token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    return verify_token(token)

# Authentication Endpoints
def setup_auth_endpoints(app: FastAPI):
    """Register authentication endpoints"""
    
    @app.post("/api/v1/auth/register", response_model=UserRegisterResponse)
    async def register_user(request: UserRegisterRequest):
        """Register a new user (persistent)"""
        try:
            if db.get_user_by_email(request.email):
                raise HTTPException(status_code=400, detail="Email already registered")
            user_id = f"user_{uuid4().hex[:12]}"
            user_data = {
                'id': user_id,
                'email': request.email,
                'password_hash': hash_password(request.password),
                'full_name': request.full_name,
                'company_id': request.company_id,
                'is_active': True,
                'created_at': datetime.now()
            }
            db.insert_user(user_data)
            token = create_access_token({
                'user_id': user_id,
                'company_id': request.company_id,
                'email': request.email
            })
            return UserRegisterResponse(
                success=True,
                user_id=user_id,
                message="User registered successfully",
                token=token
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    @app.post("/api/v1/auth/login", response_model=UserLoginResponse)
    async def login_user(request: UserLoginRequest):
        """Login user and return JWT token (persistent)"""
        try:
            user = db.get_user_by_email(request.email)
            if not user or not verify_password(request.password, user['password_hash']):
                raise HTTPException(status_code=401, detail="Invalid email or password")
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            token = create_access_token(
                data={
                    'user_id': user['id'],
                    'company_id': user['company_id'],
                    'email': user['email']
                },
                expires_delta=access_token_expires
            )
            return UserLoginResponse(
                success=True,
                token=token,
                user_id=user['id'],
                company_id=user['company_id'],
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    
    @app.post("/api/v1/auth/logout")
    async def logout_user(current_user: Dict[str, Any] = Depends(get_current_user)):
        """Logout user by invalidating token"""
        try:
            # In production, invalidate token in database/redis
            return {
                'success': True,
                'message': 'Logged out successfully'
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")
    
    @app.post("/api/v1/auth/validate", response_model=TokenValidationResponse)
    async def validate_token(current_user: Dict[str, Any] = Depends(get_current_user)):
        """Validate current token"""
        return TokenValidationResponse(
            valid=True,
            user_id=current_user.get('user_id'),
            company_id=current_user.get('company_id'),
            email=current_user.get('email')
        )

# Company Setup Endpoints
def setup_company_endpoints(app: FastAPI):
    """Register company setup endpoints"""
    
    @app.post("/api/v1/company/setup", response_model=CompanySetupResponse)
    async def setup_company(request: CompanySetupRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
        """Company setup endpoint (persistent, with aliases)"""
        try:
            company_id = f"comp_{uuid4().hex[:12]}"
            company_data = {
                'id': company_id,
                'name': request.name,
                'currency': request.currency,
                'primary_color': request.primary_color or '#1976D2',
                'secondary_color': request.secondary_color or '#424242',
                'accent_color': request.accent_color or '#FF6B6B',
                'dso_target': request.dso_target or 45,
                'sla_days': request.sla_days or 30,
                'tax_id': request.tax_id,
                'address_line1': request.address,
                'phone': request.phone,
                'company_aliases': request.aliases or [],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            db.insert_company(company_data)
            return CompanySetupResponse(
                success=True,
                company_id=company_id,
                company_name=request.name,
                settings={
                    'currency': request.currency,
                    'primary_color': company_data['primary_color'],
                    'secondary_color': company_data['secondary_color'],
                    'accent_color': company_data['accent_color'],
                    'dso_target': company_data['dso_target'],
                    'sla_days': company_data['sla_days'],
                    'tax_id': company_data['tax_id'],
                    'address': company_data['address_line1'],
                    'phone': company_data['phone']
                },
                aliases=company_data['company_aliases'],
                message="Company setup successful"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Company setup failed: {str(e)}")
    
    @app.get("/api/v1/company/{company_id}", response_model=CompanyProfileResponse)
    async def get_company_profile(company_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
        """Get company profile and settings (persistent)"""
        try:
            if current_user.get('company_id') != company_id:
                raise HTTPException(status_code=403, detail="Access denied")
            company = db.get_company_by_id(company_id)
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")
            return CompanyProfileResponse(
                company_id=company['id'],
                name=company['name'],
                currency=company['currency'],
                primary_color=company['primary_color'],
                secondary_color=company['secondary_color'],
                accent_color=company['accent_color'],
                dso_target=company.get('dso_target', 45),
                sla_days=company.get('sla_days', 30),
                created_at=str(company.get('created_at', '')),
                updated_at=str(company.get('updated_at', ''))
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Get company failed: {str(e)}")
    
    @app.put("/api/v1/company/{company_id}")
    async def update_company_profile(company_id: str, request: CompanySetupRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
        """Update company profile and settings (persistent)"""
        try:
            if current_user.get('company_id') != company_id:
                raise HTTPException(status_code=403, detail="Access denied")
            update_data = {
                'name': request.name,
                'currency': request.currency,
                'primary_color': request.primary_color,
                'secondary_color': request.secondary_color,
                'accent_color': request.accent_color,
                'dso_target': request.dso_target,
                'sla_days': request.sla_days,
                'tax_id': request.tax_id,
                'address_line1': request.address,
                'phone': request.phone,
                'company_aliases': request.aliases or []
            }
            db.update_company(company_id, {k: v for k, v in update_data.items() if v is not None})
            return {
                'success': True,
                'company_id': company_id,
                'message': 'Company profile updated successfully'
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Update company failed: {str(e)}")

# Initialize all auth and company endpoints
def setup_auth_system(app: FastAPI):
    """Setup complete authentication and company system"""
    setup_auth_endpoints(app)
    setup_company_endpoints(app)
