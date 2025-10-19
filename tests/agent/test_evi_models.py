"""
Unit tests for EVI 360 specific Pydantic models.

Tests the 7 EVI-specific models added in Phase 2:
- TieredGuideline
- GuidelineSearchResult
- EVIProduct
- ProductRecommendation
- ProductSearchResult
- ResearchAgentResponse
- SpecialistAgentResponse
"""

import pytest
from datetime import datetime
from typing import List
from pydantic import ValidationError

from agent.models import (
    TieredGuideline,
    GuidelineSearchResult,
    EVIProduct,
    ProductRecommendation,
    ProductSearchResult,
    ResearchAgentResponse,
    SpecialistAgentResponse,
)


class TestTieredGuideline:
    """Test TieredGuideline model for 3-tier workplace safety guidelines."""

    def test_tiered_guideline_valid_all_tiers(self):
        """Test valid guideline with all 3 tiers populated."""
        guideline = TieredGuideline(
            document_id="doc-123",
            title="Werken op hoogte",
            tier_1_content="Valbescherming verplicht vanaf 2.5m.",
            tier_2_content="Valharnas EN 361 gecertificeerd vereist. Inspectie elke 6 maanden.",
            tier_3_content="Volledige technische specificaties en procedures...",
            source="notion",
        )

        assert guideline.document_id == "doc-123"
        assert guideline.title == "Werken op hoogte"
        assert "Valbescherming" in guideline.tier_1_content
        assert "Valharnas" in guideline.tier_2_content
        assert "technische" in guideline.tier_3_content
        assert guideline.source == "notion"

    def test_tiered_guideline_minimal(self):
        """Test minimal guideline with only required fields."""
        guideline = TieredGuideline(
            document_id="doc-456",
            title="Minimale Richtlijn",
        )

        assert guideline.document_id == "doc-456"
        assert guideline.title == "Minimale Richtlijn"
        assert guideline.tier_1_content is None
        assert guideline.tier_2_content is None
        assert guideline.tier_3_content is None
        assert guideline.source == "notion"  # Default

    def test_tiered_guideline_empty_content_validation(self):
        """Test that empty strings are converted to None."""
        guideline = TieredGuideline(
            document_id="doc-789",
            title="Test",
            tier_1_content="   ",  # Whitespace only
            tier_2_content="",  # Empty string
            tier_3_content="Valid content",
        )

        assert guideline.tier_1_content is None
        assert guideline.tier_2_content is None
        assert guideline.tier_3_content == "Valid content"

    def test_tiered_guideline_with_metadata(self):
        """Test guideline with custom metadata."""
        metadata = {
            "author": "Safety Specialist",
            "last_reviewed": "2025-10-15",
            "compliance_standards": ["EN_795", "EN_361"],
        }

        guideline = TieredGuideline(
            document_id="doc-101",
            title="Test Guideline",
            tier_1_content="Summary",
            metadata=metadata,
        )

        assert guideline.metadata["author"] == "Safety Specialist"
        assert len(guideline.metadata["compliance_standards"]) == 2


class TestGuidelineSearchResult:
    """Test GuidelineSearchResult model for tier-aware search results."""

    def test_guideline_search_result_valid(self):
        """Test valid guideline search result."""
        result = GuidelineSearchResult(
            chunk_id="chunk-123",
            document_id="doc-456",
            document_title="Werken op hoogte",
            content="Valbescherming is verplicht vanaf 2.5 meter hoogte.",
            tier=1,
            score=0.89,
            vector_similarity=0.85,
            text_similarity=0.12,
        )

        assert result.chunk_id == "chunk-123"
        assert result.document_id == "doc-456"
        assert result.tier == 1
        assert result.score == 0.89
        assert result.vector_similarity == 0.85
        assert result.text_similarity == 0.12

    def test_guideline_search_result_tier_validation(self):
        """Test tier validation (must be 1, 2, or 3)."""
        # Valid tiers
        for tier in [1, 2, 3]:
            result = GuidelineSearchResult(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="Test",
                content="Content",
                tier=tier,
                score=0.5,
            )
            assert result.tier == tier

        # Invalid tier (Pydantic raises ValidationError, not ValueError)
        with pytest.raises(ValidationError):
            GuidelineSearchResult(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="Test",
                content="Content",
                tier=4,  # Invalid - exceeds maximum
                score=0.5,
            )

        with pytest.raises(ValidationError):
            GuidelineSearchResult(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="Test",
                content="Content",
                tier=0,  # Invalid - below minimum
                score=0.5,
            )

    def test_guideline_search_result_score_validation(self):
        """Test score validation (0.0 to 1.0)."""
        # Valid score
        result = GuidelineSearchResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_title="Test",
            content="Content",
            tier=1,
            score=0.95,
        )
        assert result.score == 0.95

        # Score out of range should fail pydantic validation
        with pytest.raises(ValidationError):
            GuidelineSearchResult(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="Test",
                content="Content",
                tier=1,
                score=1.5,  # > 1.0
            )

    def test_guideline_search_result_with_metadata(self):
        """Test search result with additional metadata."""
        result = GuidelineSearchResult(
            chunk_id="chunk-123",
            document_id="doc-456",
            document_title="Safety Guide",
            content="Content here",
            tier=2,
            score=0.75,
            metadata={"highlighted": True, "chunk_index": 5},
        )

        assert result.metadata["highlighted"] is True
        assert result.metadata["chunk_index"] == 5


class TestEVIProduct:
    """Test EVIProduct model for workplace safety equipment."""

    def test_evi_product_valid(self):
        """Test valid EVI product."""
        product = EVIProduct(
            name="Veiligheidshelm XYZ",
            description="CE-gecertificeerde helm voor bouwplaatsen volgens EN 397",
            url="https://evi360.nl/products/helm-xyz",
            category="Hoofdbescherming",
            subcategory="Helmen",
            compliance_tags=["EN_397", "CE_CERTIFIED", "FALL_PROTECTION"],
        )

        assert product.name == "Veiligheidshelm XYZ"
        assert "CE-gecertificeerd" in product.description
        assert product.url.startswith("https://")
        assert product.category == "Hoofdbescherming"
        assert len(product.compliance_tags) == 3
        assert "EN_397" in product.compliance_tags

    def test_evi_product_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        for url in ["https://evi360.nl/product", "http://example.com/item"]:
            product = EVIProduct(
                name="Test Product",
                description="Description",
                url=url,
            )
            assert product.url == url

        # Invalid URL
        with pytest.raises(ValueError, match="URL must start with http"):
            EVIProduct(
                name="Test Product",
                description="Description",
                url="invalid-url",
            )

    def test_evi_product_compliance_tags_normalization(self):
        """Test compliance tags are normalized (uppercase, underscores)."""
        product = EVIProduct(
            name="Test Product",
            description="Description",
            url="https://example.com",
            compliance_tags=["en 397", "CE Certified", "fall protection"],
        )

        # Tags should be uppercase with underscores
        assert "EN_397" in product.compliance_tags
        assert "CE_CERTIFIED" in product.compliance_tags
        assert "FALL_PROTECTION" in product.compliance_tags

    def test_evi_product_embedding_validation(self):
        """Test embedding dimension validation."""
        # Valid embedding (1536 dimensions)
        embedding = [0.1] * 1536
        product = EVIProduct(
            name="Test",
            description="Desc",
            url="https://example.com",
            embedding=embedding,
        )
        assert len(product.embedding) == 1536

        # Invalid embedding dimension
        with pytest.raises(ValueError, match="Embedding must have 1536 dimensions"):
            EVIProduct(
                name="Test",
                description="Desc",
                url="https://example.com",
                embedding=[0.1, 0.2, 0.3],  # Wrong dimension
            )

    def test_evi_product_with_metadata(self):
        """Test product with additional metadata."""
        metadata = {
            "price": 45.99,
            "stock": 150,
            "manufacturer": "SafetyPro",
            "weight_kg": 0.35,
        }

        product = EVIProduct(
            name="Safety Helmet",
            description="Premium helmet",
            url="https://example.com/helmet",
            metadata=metadata,
        )

        assert product.metadata["price"] == 45.99
        assert product.metadata["manufacturer"] == "SafetyPro"

    def test_evi_product_defaults(self):
        """Test product with default values."""
        product = EVIProduct(
            name="Minimal Product",
            description="Minimal description",
            url="https://example.com",
        )

        assert product.id is None
        assert product.category is None
        assert product.subcategory is None
        assert product.embedding is None
        assert product.compliance_tags == []
        assert product.metadata == {}
        assert product.source == "evi360_website"


class TestProductRecommendation:
    """Test ProductRecommendation model for specialist agent responses."""

    def test_product_recommendation_valid(self):
        """Test valid product recommendation."""
        product = EVIProduct(
            name="Valharnas Pro",
            description="Professioneel valharnas volgens EN 361",
            url="https://evi360.nl/valharnas-pro",
            compliance_tags=["EN_361", "FALL_PROTECTION"],
        )

        recommendation = ProductRecommendation(
            product=product,
            relevance_score=0.92,
            reasoning="Dit valharnas voldoet aan EN 361 normen voor werken op hoogte.",
            matching_compliance_tags=["EN_361"],
        )

        assert recommendation.product.name == "Valharnas Pro"
        assert recommendation.relevance_score == 0.92
        assert "EN 361" in recommendation.reasoning
        assert "EN_361" in recommendation.matching_compliance_tags

    def test_product_recommendation_score_validation(self):
        """Test relevance score validation."""
        product = EVIProduct(
            name="Test", description="Desc", url="https://example.com"
        )

        # Valid score
        rec = ProductRecommendation(product=product, relevance_score=0.75)
        assert rec.relevance_score == 0.75

        # Edge cases - exact boundaries
        rec = ProductRecommendation(product=product, relevance_score=0.0)
        assert rec.relevance_score == 0.0

        rec = ProductRecommendation(product=product, relevance_score=1.0)
        assert rec.relevance_score == 1.0

        # Out of range scores should raise ValidationError
        with pytest.raises(ValidationError):
            ProductRecommendation(product=product, relevance_score=1.5)

        with pytest.raises(ValidationError):
            ProductRecommendation(product=product, relevance_score=-0.3)

    def test_product_recommendation_dutch_reasoning(self):
        """Test recommendation with Dutch language reasoning."""
        product = EVIProduct(
            name="Veiligheidsschoenen S3",
            description="Veiligheidsschoenen met stalen neus",
            url="https://example.com",
            compliance_tags=["S3_CERTIFIED", "TOE_PROTECTION"],
        )

        recommendation = ProductRecommendation(
            product=product,
            relevance_score=0.88,
            reasoning="Deze schoenen bieden uitstekende bescherming voor werkomgevingen met zware objecten.",
        )

        assert "bescherming" in recommendation.reasoning


class TestProductSearchResult:
    """Test ProductSearchResult model for database search results."""

    def test_product_search_result_valid(self):
        """Test valid product search result."""
        result = ProductSearchResult(
            product_id="prod-123",
            name="Veiligheidshelm",
            description="Professionele helm",
            url="https://example.com/helm",
            category="Hoofdbescherming",
            similarity=0.87,
            compliance_tags=["EN_397", "CE_CERTIFIED"],
            metadata={"color": "yellow", "size": "adjustable"},
        )

        assert result.product_id == "prod-123"
        assert result.name == "Veiligheidshelm"
        assert result.similarity == 0.87
        assert len(result.compliance_tags) == 2
        assert result.metadata["color"] == "yellow"

    def test_product_search_result_similarity_validation(self):
        """Test similarity score validation."""
        # Valid similarity
        result = ProductSearchResult(
            product_id="p1",
            name="Product",
            description="Desc",
            url="https://example.com",
            similarity=0.95,
        )
        assert result.similarity == 0.95

        # Invalid similarity (out of range)
        with pytest.raises(ValidationError):
            ProductSearchResult(
                product_id="p1",
                name="Product",
                description="Desc",
                url="https://example.com",
                similarity=1.2,  # > 1.0
            )


class TestResearchAgentResponse:
    """Test ResearchAgentResponse model for research agent output."""

    def test_research_agent_response_valid(self):
        """Test valid research agent response with guidelines and products."""
        guideline = GuidelineSearchResult(
            chunk_id="c1",
            document_id="d1",
            document_title="Safety Guide",
            content="Safety content",
            tier=1,
            score=0.9,
        )

        product = ProductSearchResult(
            product_id="p1",
            name="Product",
            description="Desc",
            url="https://example.com",
            similarity=0.85,
        )

        response = ResearchAgentResponse(
            guidelines=[guideline],
            products=[product],
            query="werken op hoogte",
            search_metadata={"search_time_ms": 150, "total_results": 10},
        )

        assert len(response.guidelines) == 1
        assert len(response.products) == 1
        assert response.query == "werken op hoogte"
        assert response.search_metadata["search_time_ms"] == 150

    def test_research_agent_response_empty_results(self):
        """Test research agent response with no results."""
        response = ResearchAgentResponse(
            guidelines=[],
            products=[],
            query="obscure query",
        )

        assert len(response.guidelines) == 0
        assert len(response.products) == 0
        assert response.search_metadata == {}

    def test_research_agent_response_guidelines_only(self):
        """Test response with only guidelines (no products)."""
        guidelines = [
            GuidelineSearchResult(
                chunk_id=f"c{i}",
                document_id="d1",
                document_title="Guide",
                content=f"Content {i}",
                tier=i + 1,
                score=0.8,
            )
            for i in range(3)
        ]

        response = ResearchAgentResponse(
            guidelines=guidelines,
            products=[],
            query="test query",
        )

        assert len(response.guidelines) == 3
        assert len(response.products) == 0


class TestSpecialistAgentResponse:
    """Test SpecialistAgentResponse model for intervention specialist output."""

    def test_specialist_agent_response_valid(self):
        """Test valid specialist agent response in Dutch."""
        guideline = GuidelineSearchResult(
            chunk_id="c1",
            document_id="d1",
            document_title="Werken op hoogte",
            content="Valbescherming verplicht",
            tier=1,
            score=0.9,
        )

        product = EVIProduct(
            name="Valharnas", description="Professioneel harnas", url="https://example.com"
        )

        recommendation = ProductRecommendation(
            product=product,
            relevance_score=0.88,
            reasoning="Geschikt voor werken op hoogte",
        )

        response = SpecialistAgentResponse(
            message="Voor werken op hoogte heeft u valbescherming nodig vanaf 2.5 meter.",
            guidelines_cited=[guideline],
            product_recommendations=[recommendation],
            compliance_requirements=["EN_361", "EN_795"],
            session_id="session-123",
        )

        assert "valbescherming" in response.message.lower()
        assert len(response.guidelines_cited) == 1
        assert len(response.product_recommendations) == 1
        assert "EN_361" in response.compliance_requirements
        assert response.session_id == "session-123"

    def test_specialist_agent_response_minimal(self):
        """Test minimal specialist response (message only)."""
        response = SpecialistAgentResponse(
            message="Ik kan geen relevante informatie vinden.",
            session_id="session-456",
        )

        assert response.message
        assert len(response.guidelines_cited) == 0
        assert len(response.product_recommendations) == 0
        assert len(response.compliance_requirements) == 0

    def test_specialist_agent_response_dutch_language(self):
        """Test that specialist response is in Dutch."""
        dutch_message = """
        Voor werken op hoogte vanaf 2.5 meter zijn de volgende maatregelen verplicht:
        1. Gebruik van gecertificeerd valharnas (EN 361)
        2. Ankerpunten volgens EN 795
        3. Jaarlijkse training en inspectie
        """

        response = SpecialistAgentResponse(
            message=dutch_message,
            session_id="session-789",
            compliance_requirements=["EN_361", "EN_795"],
        )

        # Check for Dutch keywords
        assert "verplicht" in response.message
        assert "gecertificeerd" in response.message

    def test_specialist_agent_response_with_metadata(self):
        """Test specialist response with additional metadata."""
        response = SpecialistAgentResponse(
            message="Test response",
            session_id="session-101",
            metadata={
                "query_intent": "product_recommendation",
                "confidence": 0.92,
                "language": "nl",
            },
        )

        assert response.metadata["language"] == "nl"
        assert response.metadata["confidence"] == 0.92


class TestConfigNotionConfig:
    """Test NotionConfig configuration class."""

    def test_notion_config_headers(self):
        """Test that NotionConfig generates correct headers."""
        from config.notion_config import NotionConfig

        config = NotionConfig(
            api_token="secret_test_token",
            guidelines_database_id="a" * 32,  # 32 hex chars
        )

        headers = config.get_headers()

        assert headers["Authorization"] == "Bearer secret_test_token"
        assert headers["Notion-Version"] == "2022-06-28"
        assert headers["Content-Type"] == "application/json"

    def test_notion_config_database_id_validation(self):
        """Test database ID validation."""
        from config.notion_config import NotionConfig

        # Valid database ID (32 hex characters)
        config = NotionConfig(
            api_token="token", guidelines_database_id="a1b2c3d4" * 4  # 32 chars
        )
        assert config.validate_database_id() is True

        # Valid with hyphens
        config = NotionConfig(
            api_token="token",
            guidelines_database_id="a1b2c3d4-1234-5678-9abc-def012345678",
        )
        assert config.validate_database_id() is True

        # Invalid (too short)
        config = NotionConfig(api_token="token", guidelines_database_id="short")
        assert config.validate_database_id() is False

        # Invalid (non-hex characters)
        config = NotionConfig(
            api_token="token", guidelines_database_id="x" * 32
        )
        assert config.validate_database_id() is False

    def test_notion_config_defaults(self):
        """Test NotionConfig default values."""
        from config.notion_config import NotionConfig

        config = NotionConfig(
            api_token="token", guidelines_database_id="a" * 32
        )

        assert config.base_url == "https://api.notion.com/v1"
        assert config.notion_version == "2022-06-28"
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.page_size == 100
