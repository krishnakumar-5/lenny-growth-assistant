import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ship30 import Ship30Request, Ship30Response
from app.services.llm import get_llm_client
from app.services.llm.base import (
    CloudProviderConfigurationError,
    LLMGenerationError,
    OllamaModelNotFoundError,
    OllamaUnavailableError,
)
from app.services.skills.ship30_skill import (
    InsufficientTranscriptEvidenceError,
    Ship30EssaySkill,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["skills"])


@router.post(
    "/skills/ship30-essay",
    response_model=Ship30Response,
    status_code=status.HTTP_200_OK,
    summary="Generate Grounded Ship 30 for 30 Atomic Essay",
    description=(
        "Retrieves verified podcast transcript evidence for a product/growth topic, "
        "and synthesizes a high-impact, 200-300 word 'Atomic Essay' adhering strictly "
        "to the Ship 30 for 30 digital writing framework by Dickie Bush & Nicolas Cole."
    ),
)
async def generate_ship30_essay(
    request: Ship30Request,
    db: Session = Depends(get_db),
) -> Ship30Response:
    """Generate a grounded Ship 30 for 30 Atomic Essay artifact."""
    # 1. Resolve LLM client
    try:
        llm_client = get_llm_client(
            provider_name=request.provider,
            model_name=request.model,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # 2. Instantiate and execute Ship 30 Skill
    skill = Ship30EssaySkill(llm_client=llm_client)

    try:
        response = await skill.generate_essay(db=db, request=request)
        return response
    except InsufficientTranscriptEvidenceError as e:
        logger.warning("Ship 30 essay generation refused due to lack of evidence: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )
    except OllamaUnavailableError as e:
        logger.error("Ollama connection failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except OllamaModelNotFoundError as e:
        logger.error("Ollama model missing: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except CloudProviderConfigurationError as e:
        logger.error("Cloud provider error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except LLMGenerationError as e:
        logger.error("LLM generation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate essay via LLM: {str(e)}",
        )
