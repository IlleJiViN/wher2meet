from typing import List, Optional
from pydantic import BaseModel, Field

class UserCoordinate(BaseModel):
    name: str = Field(..., description="Name of the user origin.")
    latitude: float = Field(..., description="Latitude of the origin.")
    longitude: float = Field(..., description="Longitude of the origin.")
    weight: float = Field(1.0, description="Preference weight. Higher weight pulls the midpoint closer to this user.")


class SearchRequest(BaseModel):
    query: str
    user_latitude: float | None = None
    user_longitude: float | None = None
    users: List[UserCoordinate] | None = None
    radius_meters: float = 1000.0
    category_threshold: float = 0.35
    similarity_threshold: float = 0.25
    top_k: int = 3
    engine_version: str = "v5"
    routing_mode: str = Field("distance", description="Routing mode: 'distance' (straight line) or 'time' (OSRM travel time)")


class PlaceSearchResult(BaseModel):
    place_id: int = Field(..., description="Unique identifier for the location.")
    name: str = Field(..., description="Name of the place.")
    category: str = Field(..., description="Category (e.g., Cafe, PC room, Studio).")
    latitude: float = Field(..., description="Latitude coordinate.")
    longitude: float = Field(..., description="Longitude coordinate.")
    description: str = Field(..., description="Detailed description of the location.")
    address: str = Field("", description="Street address of the location.")
    distance_meters: float = Field(..., description="Geographical distance in meters from the user.")
    similarity_score: float = Field(..., description="Combined similarity score (0.0 to 1.0).")
    category_score: float = Field(0.0, description="Category prototype similarity score.")
    name_score: float = Field(0.0, description="Place name similarity score.")


class SearchResponse(BaseModel):
    query: str = Field(..., description="The original query string.")
    matched_categories: List[str] = Field(default=[], description="Categories that matched the query intent.")
    results: List[PlaceSearchResult] = Field(..., description="List of matched places ranked by relevance within the radius.")
    latency_ms: float = Field(..., description="Search process latency in milliseconds.")
    system_message: Optional[str] = Field(default=None, description="System message for the frontend to display.")
