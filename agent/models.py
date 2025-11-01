"""
Pydantic models for data validation and serialization.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SearchType(str, Enum):
    """Search type enumeration."""
    VECTOR = "vector"
    HYBRID = "hybrid"
    GRAPH = "graph"


# Request Models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User identifier")
    language: Literal["nl", "en"] = Field(default="nl", description="Response language: 'nl' (Dutch) or 'en' (English)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    search_type: SearchType = Field(default=SearchType.HYBRID, description="Type of search to perform")

    model_config = ConfigDict(use_enum_values=True)


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(default=SearchType.HYBRID, description="Type of search")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    
    model_config = ConfigDict(use_enum_values=True)


# Response Models
class DocumentMetadata(BaseModel):
    """Document metadata model."""
    id: str
    title: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    chunk_count: Optional[int] = None


class ChunkResult(BaseModel):
    """Chunk search result model."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_title: str
    document_source: str
    source_url: Optional[str] = None

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure score is between 0 and 1."""
        return max(0.0, min(1.0, v))


class GraphSearchResult(BaseModel):
    """Knowledge graph search result model."""
    fact: str
    uuid: str
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    source_node_uuid: Optional[str] = None


class EntityRelationship(BaseModel):
    """Entity relationship model."""
    from_entity: str
    to_entity: str
    relationship_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Search response model."""
    results: List[ChunkResult] = Field(default_factory=list)
    graph_results: List[GraphSearchResult] = Field(default_factory=list)
    total_results: int = 0
    search_type: SearchType
    query_time_ms: float


class ToolCall(BaseModel):
    """Tool call information model."""
    tool_name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    tool_call_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    session_id: str
    sources: List[DocumentMetadata] = Field(default_factory=list)
    tools_used: List[ToolCall] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamDelta(BaseModel):
    """Streaming response delta."""
    content: str
    delta_type: Literal["text", "tool_call", "end"] = "text"
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Database Models
class Document(BaseModel):
    """Document model."""
    id: Optional[str] = None
    title: str
    source: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Chunk(BaseModel):
    """Document chunk model."""
    id: Optional[str] = None
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_count: Optional[int] = None
    created_at: Optional[datetime] = None
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        """Validate embedding dimensions."""
        if v is not None and len(v) != 1536:  # OpenAI text-embedding-3-small
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(v)}")
        return v


class Session(BaseModel):
    """Session model."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class Message(BaseModel):
    """Message model."""
    id: Optional[str] = None
    session_id: str
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(use_enum_values=True)


# Agent Models
class AgentDependencies(BaseModel):
    """Dependencies for the agent."""
    session_id: str
    database_url: Optional[str] = None
    neo4j_uri: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)




class AgentContext(BaseModel):
    """Agent execution context."""
    session_id: str
    messages: List[Message] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    search_results: List[ChunkResult] = Field(default_factory=list)
    graph_results: List[GraphSearchResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Ingestion Models
class IngestionConfig(BaseModel):
    """Configuration for document ingestion."""
    chunk_size: int = Field(default=1000, ge=100, le=5000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    max_chunk_size: int = Field(default=2000, ge=500, le=10000)
    use_semantic_chunking: bool = True
    extract_entities: bool = True
    # New option for faster ingestion
    skip_graph_building: bool = Field(default=False, description="Skip knowledge graph building for faster ingestion")
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Ensure overlap is less than chunk size."""
        chunk_size = info.data.get('chunk_size', 1000)
        if v >= chunk_size:
            raise ValueError(f"Chunk overlap ({v}) must be less than chunk size ({chunk_size})")
        return v


class IngestionResult(BaseModel):
    """Result of document ingestion."""
    document_id: str
    title: str
    chunks_created: int
    entities_extracted: int
    relationships_created: int
    processing_time_ms: float
    errors: List[str] = Field(default_factory=list)


# Error Models
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


# Health Check Models
class HealthStatus(BaseModel):
    """Health check status."""
    status: Literal["healthy", "degraded", "unhealthy"]
    database: bool
    graph_database: bool
    llm_connection: bool
    version: str
    timestamp: datetime


# =============================================================================
# EVI 360 Specific Models
# =============================================================================

class TieredGuideline(BaseModel):
    """
    Tiered guideline model for EVI 360 workplace safety guidelines.

    Guidelines are structured in 3 tiers:
    - Tier 1: Summary/Overview (always shown first)
    - Tier 2: Key Facts (shown for deeper understanding)
    - Tier 3: Detailed Content (full technical details)
    """
    document_id: str
    title: str
    tier_1_content: Optional[str] = Field(None, description="Summary/overview content")
    tier_2_content: Optional[str] = Field(None, description="Key facts content")
    tier_3_content: Optional[str] = Field(None, description="Detailed technical content")
    source: str = Field(default="notion", description="Source of the guideline")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    @field_validator('tier_1_content', 'tier_2_content', 'tier_3_content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        """Ensure content is not empty if provided."""
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class GuidelineSearchResult(BaseModel):
    """Search result for tiered guidelines."""
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    tier: int = Field(..., ge=1, le=3, description="Guideline tier (1-3)")
    score: float = Field(..., ge=0.0, le=1.0, description="Search relevance score")
    vector_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    text_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('tier')
    @classmethod
    def validate_tier(cls, v: int) -> int:
        """Validate tier is 1, 2, or 3."""
        if v not in [1, 2, 3]:
            raise ValueError("Tier must be 1 (summary), 2 (key facts), or 3 (details)")
        return v


class EVIProduct(BaseModel):
    """
    EVI 360 product model.

    Represents workplace safety products from the EVI 360 catalog.
    """
    id: Optional[str] = None
    name: str = Field(..., min_length=1, description="Product name")
    description: str = Field(..., min_length=1, description="Product description")
    url: str = Field(..., description="Product page URL on EVI 360 website")
    category: Optional[str] = Field(None, description="Product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    embedding: Optional[List[float]] = None
    compliance_tags: List[str] = Field(
        default_factory=list,
        description="Compliance and safety tags (e.g., ['EN_361', 'CE_certified', 'fall_protection'])"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (price, specs, availability)"
    )
    source: str = Field(default="evi360_website", description="Data source")
    last_scraped_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is properly formatted."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        """Validate embedding dimensions."""
        if v is not None and len(v) != 1536:
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(v)}")
        return v

    @field_validator('compliance_tags')
    @classmethod
    def validate_compliance_tags(cls, v: List[str]) -> List[str]:
        """Ensure compliance tags are uppercase and properly formatted."""
        return [tag.strip().upper().replace(' ', '_') for tag in v if tag.strip()]


class ProductRecommendation(BaseModel):
    """
    Product recommendation with relevance scoring.

    Used by the Intervention Specialist Agent to recommend
    relevant EVI products based on workplace safety queries.
    """
    product: EVIProduct
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to query")
    reasoning: Optional[str] = Field(
        None,
        description="Why this product is recommended (in Dutch)"
    )
    matching_compliance_tags: List[str] = Field(
        default_factory=list,
        description="Compliance tags that match the query requirements"
    )

    @field_validator('relevance_score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure score is between 0 and 1."""
        return max(0.0, min(1.0, v))


class ProductSearchResult(BaseModel):
    """Product search result from database."""
    product_id: str
    name: str
    description: str
    url: str
    category: Optional[str] = None
    similarity: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score")
    compliance_tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchAgentResponse(BaseModel):
    """
    Response from the Research Agent.

    The Research Agent searches guidelines and products,
    providing structured data to the Intervention Specialist.
    """
    guidelines: List[GuidelineSearchResult] = Field(
        default_factory=list,
        description="Relevant guidelines found"
    )
    products: List[ProductSearchResult] = Field(
        default_factory=list,
        description="Relevant products found"
    )
    query: str = Field(..., description="Original search query")
    search_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Search performance and filter metadata"
    )


class SpecialistAgentResponse(BaseModel):
    """
    Response from the Intervention Specialist Agent.

    Structured Dutch-language response with guidelines,
    recommendations, and product suggestions.
    """
    message: str = Field(..., description="Main response message in Dutch")
    guidelines_cited: List[GuidelineSearchResult] = Field(
        default_factory=list,
        description="Guidelines referenced in the response"
    )
    product_recommendations: List[ProductRecommendation] = Field(
        default_factory=list,
        description="Recommended EVI products"
    )
    compliance_requirements: List[str] = Field(
        default_factory=list,
        description="Key compliance requirements mentioned"
    )
    session_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# FEAT-003 MVP Specialist Agent Models (Simplified)
# =============================================================================

class SpecialistDeps(BaseModel):
    """
    Dependencies for specialist agent.

    Simplified for MVP - just session and user tracking.
    """
    session_id: str
    user_id: str = Field(default="cli_user")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Citation(BaseModel):
    """Citation model for specialist agent responses."""
    title: str = Field(default="Unknown Source", description="Guideline title")
    url: Optional[str] = Field(None, description="Source URL if available")
    quote: Optional[str] = Field(None, description="Relevant quote or summary")


class SpecialistResponse(BaseModel):
    """
    Simplified specialist response for FEAT-003 MVP.

    Dutch-language response with citations but no products/tiers.

    FEAT-010: Fields have defaults to support streaming partial validation.
    OpenAI sends incremental JSON: {} → {"content": ""} → {"content": "A"} → ...
    """
    content: str = Field(default="", description="Main response in Dutch")
    citations: List[Citation] = Field(default_factory=list, description="Minimum 2 citations")
    search_metadata: Dict[str, Any] = Field(default_factory=dict, description="Search stats")


# =============================================================================
# FEAT-007: OpenAI-Compatible Models for OpenWebUI Integration
# =============================================================================

class OpenAIChatMessage(BaseModel):
    """Single message in OpenAI chat format."""
    role: Literal["system", "user", "assistant"]
    content: str


class OpenAIChatRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field(description="Model ID (e.g., 'evi-specialist')")
    messages: List[OpenAIChatMessage] = Field(description="Conversation history")
    stream: bool = Field(default=False, description="Enable SSE streaming")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2000, ge=1)


class OpenAIChatResponseMessage(BaseModel):
    """Message in OpenAI chat completion response."""
    role: Literal["assistant"] = "assistant"
    content: str


class OpenAIChatResponseChoice(BaseModel):
    """Single response choice in OpenAI format."""
    index: int = 0
    message: OpenAIChatResponseMessage
    finish_reason: str = "stop"


class OpenAIChatResponse(BaseModel):
    """OpenAI-compatible chat completion response (non-streaming)."""
    id: str = Field(description="Unique completion ID")
    object: str = "chat.completion"
    created: int = Field(description="Unix timestamp")
    model: str = "evi-specialist"
    choices: List[OpenAIChatResponseChoice]
    usage: Optional[Dict[str, int]] = None  # Optional token usage stats


class OpenAIStreamDelta(BaseModel):
    """Delta content in streaming chunk."""
    role: Optional[str] = None
    content: Optional[str] = None


class OpenAIStreamChoice(BaseModel):
    """Choice in streaming chunk."""
    index: int = 0
    delta: OpenAIStreamDelta
    finish_reason: Optional[str] = None


class OpenAIStreamChunk(BaseModel):
    """Single SSE chunk in OpenAI streaming format."""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str = "evi-specialist"
    choices: List[OpenAIStreamChoice]


class OpenAIError(BaseModel):
    """OpenAI-compatible error format."""
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None


class OpenAIErrorResponse(BaseModel):
    """OpenAI error response wrapper."""
    error: OpenAIError


class OpenAIModel(BaseModel):
    """OpenAI model object."""
    id: str
    object: str = "model"
    created: int
    owned_by: str


class OpenAIModelList(BaseModel):
    """OpenAI models list response."""
    object: str = "list"
    data: List[OpenAIModel]