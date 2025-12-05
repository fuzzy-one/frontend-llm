# api/models.py - Pydantic models for API request/response
# Rich models designed for frontend UI display

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# =============================================================================
# REQUEST MODELS
# =============================================================================

class SearchRequest(BaseModel):
    """Search request with natural language query"""
    query: str = Field(..., description="Natural language search query")
    size: int = Field(25, ge=1, le=100, description="Number of results")


# =============================================================================
# FILTER MODELS
# =============================================================================

class SearchFeatures(BaseModel):
    """Feature preferences (pet friendly, parking, etc.)"""
    animale: Optional[str] = None  # WANT, EXCLUDE, or None
    fumatori: Optional[str] = None
    parcare: Optional[str] = None
    mobilat: Optional[str] = None
    centrala: Optional[str] = None


class SearchFilters(BaseModel):
    """Parsed search filters from LLM"""
    location: Optional[str] = None
    city: Optional[str] = None
    transaction: Optional[str] = None
    property_type: Optional[str] = None
    rooms: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    keywords: List[str] = []
    features: SearchFeatures = Field(default_factory=SearchFeatures)


# =============================================================================
# RESULT MODELS - Rich data for UI cards
# =============================================================================

class ListingCoordinates(BaseModel):
    """Geographic coordinates"""
    lat: Optional[float] = None
    lng: Optional[float] = None


class ListingAttributes(BaseModel):
    """Property attributes extracted from listing"""
    surface: Optional[str] = None
    floor: Optional[str] = None
    rooms: Optional[str] = None
    bathrooms: Optional[str] = None
    layout: Optional[str] = None  # decomandat/semidecomandat
    condition: Optional[str] = None
    heating: Optional[str] = None
    appliances: Optional[str] = None
    parking: Optional[str] = None
    year_built: Optional[str] = None
    availability: Optional[str] = None


class SearchResult(BaseModel):
    """Single search result - rich data for UI card display"""
    
    # Identity
    id: str = Field(..., description="Unique document ID")
    ad_id: Optional[str] = Field(None, description="Original ad ID from source")
    
    # Main content
    title: str = Field(..., description="Listing title")
    description: str = Field(..., description="Listing description (truncated)")
    
    # Price
    price: Optional[float] = None
    currency: str = "EUR"
    
    # Location
    location_1: Optional[str] = Field(None, description="County/Region (e.g., Bucuresti, Cluj)")
    location_2: Optional[str] = Field(None, description="City/Sector (e.g., Sector 3, Cluj-Napoca)")
    location_3: Optional[str] = Field(None, description="Neighborhood (e.g., Titan, Pallady)")
    location_display: str = Field("", description="Formatted location for display")
    coordinates: Optional[ListingCoordinates] = None
    
    # Categories (as tags)
    categories: List[str] = Field(default_factory=list, description="Category tags: Vanzare, Apartamente, 3 camere")
    
    # Media
    images: List[str] = Field(default_factory=list, description="Image URLs")
    image_count: int = Field(0, description="Total number of images")
    thumbnail: Optional[str] = Field(None, description="Primary thumbnail URL")
    
    # Contact & Source
    phone: Optional[str] = Field(None, description="Contact phone number")
    source: Optional[str] = Field(None, description="Source platform (romimo, etc.)")
    url: Optional[str] = Field(None, description="Original listing URL")
    
    # Dates
    valid_from: Optional[str] = Field(None, description="Listing date")
    
    # Relevance
    relevance_score: float = Field(0.0, description="Raw search score")
    relevance_pct: float = Field(0.0, description="Relevance percentage (0-100)")
    relevance_tag: str = Field("⚪", description="Relevance emoji indicator")
    
    # Rich attributes
    attributes: ListingAttributes = Field(default_factory=ListingAttributes)


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class SearchResponse(BaseModel):
    """Full search response"""
    success: bool = True
    query: str
    parsed_filters: SearchFilters
    total: int
    results: List[SearchResult]
    session_id: str
    user_id: str


class SessionInfo(BaseModel):
    """Session state information"""
    user_id: str
    session_id: str
    filters: SearchFilters
    query_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class HistoryItem(BaseModel):
    """Single query history item"""
    query: str
    timestamp: str


class UserInfo(BaseModel):
    """Current user information"""
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    roles: List[str] = []
    groups: List[str] = []
    is_anonymous: bool = False
