"""
Requirement Extraction, Classification, Duplicate Detection, and Batch Acceptance Service.
"""

import re
from pathlib import Path
from typing import List
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.extractors.base import ExtractedDocumentText
from app.core.extractors.factory import ExtractorFactory
from app.models.document import Document
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_repository import RequirementRepository
from app.schemas.extraction import (
    BatchAcceptRequest,
    BatchAcceptResponse,
    CandidateRequirement,
    ExtractionResponse,
)
from app.schemas.requirement import RequirementResponse
from app.utils.logger import get_logger

logger = get_logger("srsense.extraction_service")

# Regex pattern for explicit requirement IDs (e.g. FR-001, NFR-02, BR-100, REQ-12)
REQ_ID_PATTERN = re.compile(r"\b([A-Z]{2,4}-\d{1,4})\b", re.IGNORECASE)

# Modal verb indicator pattern
MODAL_PATTERN = re.compile(r"\b(shall|must|should|will)\b", re.IGNORECASE)

# Numbered / Bullet list item indicator pattern
LIST_PATTERN = re.compile(r"^\s*(?:\d+[\.\)]|[\*\-•])\s+", re.IGNORECASE)


def compute_jaccard_similarity(text1: str, text2: str) -> float:
    """Compute token-based Jaccard similarity score between two texts (0.0 to 1.0)."""
    tokens1 = set(re.findall(r"\b\w+\b", text1.lower()))
    tokens2 = set(re.findall(r"\b\w+\b", text2.lower()))
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return round(intersection / union, 2)


def classify_requirement_type(text: str) -> RequirementType:
    """Classify requirement text into standard RequirementType using explainable heuristics."""
    t_lower = text.lower()

    # User Story syntax check
    if "as a " in t_lower and ("i want " in t_lower or "i need " in t_lower or "so that " in t_lower):
        return RequirementType.USER

    # Non-Functional Requirement keywords
    nfr_keywords = [
        "latency",
        "response time",
        "milliseconds",
        "ms",
        "seconds",
        "sec",
        "uptime",
        "throughput",
        "concurrent",
        "performance",
        "security",
        "encryption",
        "availability",
        "bandwidth",
        "storage",
    ]
    if any(re.search(r"\b" + re.escape(kw) + r"\b", t_lower) for kw in nfr_keywords):
        return RequirementType.NON_FUNCTIONAL

    # Business Requirement keywords
    business_keywords = [
        "revenue",
        "roi",
        "objective",
        "business goal",
        "market share",
        "cost reduction",
        "profit",
        "stakeholder",
    ]
    if any(re.search(r"\b" + re.escape(kw) + r"\b", t_lower) for kw in business_keywords):
        return RequirementType.BUSINESS

    # System Requirement keywords
    system_keywords = [
        "architecture",
        "database schema",
        "cpu",
        "memory",
        "hardware",
        "operating system",
        "os",
        "linux",
        "windows",
        "protocol",
    ]
    if any(re.search(r"\b" + re.escape(kw) + r"\b", t_lower) for kw in system_keywords):
        return RequirementType.SYSTEM

    return RequirementType.FUNCTIONAL


def infer_requirement_priority(text: str) -> RequirementPriority:
    """Infer requirement priority from text context, or default to MEDIUM."""
    t_lower = text.lower()
    if "critical" in t_lower or "must have" in t_lower or "urgently" in t_lower:
        return RequirementPriority.CRITICAL
    if "high priority" in t_lower or "vital" in t_lower or "essential" in t_lower or "mandatory" in t_lower:
        return RequirementPriority.HIGH
    if "low priority" in t_lower or "optional" in t_lower or "nice to have" in t_lower or "could have" in t_lower:
        return RequirementPriority.LOW
    return RequirementPriority.MEDIUM


def generate_candidate_title(text: str, original_id: str | None = None) -> str:
    """Generate concise title from requirement candidate statement."""
    clean_text = re.sub(r"^\s*(?:\d+[\.\)]|[\*\-•]|\b[A-Z]{2,4}-\d{1,4}\b[:\.\-]?)\s*", "", text).strip()
    words = clean_text.split()
    snippet = " ".join(words[:8]) if words else "Requirement Specification"
    if len(snippet) > 75:
        snippet = snippet[:72] + "..."
    snippet = snippet.rstrip(".")
    if original_id:
        return f"{original_id.upper()}: {snippet.capitalize()}"
    return snippet.capitalize()


class ExtractionService:
    """Service layer for document requirement extraction and candidate management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)

    async def _verify_project_ownership(self, project_id: UUID, user: User):
        """Verify project belongs to current authenticated user."""
        project = await self.project_repo.get_by_id_and_owner(
            project_id=project_id, owner_id=user.id
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )
        return project

    async def extract_candidates_from_document(
        self, user: User, project_id: UUID, document_id: UUID
    ) -> ExtractionResponse:
        """Run requirement statement identification, classification, and duplicate detection."""
        project = await self._verify_project_ownership(project_id, user)
        doc = await self.doc_repo.get_by_id_and_project(document_id, project_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        file_path = Path(doc.storage_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document storage file missing on disk",
            )

        # 1. Extract text segments
        extractor = ExtractorFactory.get_extractor(doc.file_type.value)
        extracted: ExtractedDocumentText = extractor.extract_text(file_path)

        # 2. Fetch existing project requirements for duplicate detection
        existing_reqs = await self.req_repo.get_all_by_project(project_id)

        candidates: List[CandidateRequirement] = []
        seen_statements = set()

        for segment in extracted.segments:
            # Split segment into candidate lines / sentences
            lines = [l.strip() for l in segment.text.split("\n") if l.strip()]

            for line in lines:
                if len(line) < 15 or line in seen_statements:
                    continue

                line_lower = line.lower()

                # Check requirement candidate criteria
                id_match = REQ_ID_PATTERN.search(line)
                has_modal = bool(MODAL_PATTERN.search(line))
                is_list_item = bool(LIST_PATTERN.search(line))
                is_user_story = "as a " in line_lower and ("i want " in line_lower or "i need " in line_lower)

                # Must match explicit ID OR modal verb OR list item OR user story syntax
                if not (id_match or has_modal or is_list_item or is_user_story):
                    continue

                seen_statements.add(line)
                orig_id = id_match.group(1).upper() if id_match else None
                cand_type = classify_requirement_type(line)
                cand_priority = infer_requirement_priority(line)
                cand_title = generate_candidate_title(line, orig_id)

                # Duplicate Detection (Jaccard similarity >= 0.75)
                is_dup = False
                dup_of_id = None
                max_sim = 0.0

                for ex in existing_reqs:
                    sim_desc = compute_jaccard_similarity(line, ex.description)
                    sim_title = compute_jaccard_similarity(line, ex.title)
                    sim = max(sim_desc, sim_title)
                    if sim > max_sim:
                        max_sim = sim
                        if sim >= 0.75:
                            is_dup = True
                            dup_of_id = ex.id

                cand = CandidateRequirement(
                    candidate_id=f"cand_{uuid4().hex[:8]}",
                    original_req_id=orig_id,
                    title=cand_title,
                    description=line,
                    type=cand_type,
                    priority=cand_priority,
                    source_document_id=doc.id,
                    source_section=segment.location_label,
                    source_snippet=line[:300],
                    location_label=segment.location_label,
                    is_duplicate=is_dup,
                    duplicate_of_id=dup_of_id,
                    similarity_score=max_sim,
                )
                candidates.append(cand)

        logger.info(
            "Extracted %d candidate requirements from document %s",
            len(candidates),
            doc.filename,
        )

        return ExtractionResponse(
            document_id=doc.id,
            total_candidates=len(candidates),
            candidates=candidates,
        )

    async def batch_accept_candidates(
        self, user: User, project_id: UUID, request: BatchAcceptRequest
    ) -> BatchAcceptResponse:
        """Persist accepted candidate requirements into PostgreSQL in a single atomic transaction."""
        project = await self._verify_project_ownership(project_id, user)

        created_reqs: List[Requirement] = []

        for item in request.items:
            req = Requirement(
                id=uuid4(),
                title=item.title,
                description=item.description,
                type=item.type,
                priority=item.priority,
                status=item.status,
                version="1.0",
                source="SRS Ingestion",
                source_document_id=item.source_document_id,
                source_section=item.source_section,
                source_snippet=item.source_snippet,
                original_req_id=item.original_req_id,
                project_id=project_id,
            )
            self.db.add(req)
            created_reqs.append(req)

        # Atomically increment project requirement_count
        project.requirement_count += len(request.items)

        # Single atomic transaction commit
        await self.db.commit()

        for req in created_reqs:
            await self.db.refresh(req)

        logger.info(
            "Batch accepted %d requirements for project %s (Total count: %d)",
            len(created_reqs),
            project_id,
            project.requirement_count,
        )

        return BatchAcceptResponse(
            accepted_count=len(created_reqs),
            created_requirements=[RequirementResponse.model_validate(r) for r in created_reqs],
        )
