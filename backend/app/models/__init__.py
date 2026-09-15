# backend/app/models — SQLAlchemy ORM models
from app.models.user import User, UserRole
from app.models.refresh_token import RefreshToken
from app.models.project import Project, ProjectStatus
from app.models.requirement import (
    Requirement,
    RequirementType,
    RequirementPriority,
    RequirementStatus,
)
from app.models.document import (
    Document,
    DocumentFileType,
    DocumentStatus,
)
from app.models.relationship import (
    RequirementRelationship,
    RelationshipType,
)
from app.models.suggestion import (
    RequirementSuggestion,
    SuggestionStatus,
)
from app.models.impact_report import (
    RequirementImpactReport,
    ChangeType,
)
from app.models.verification import (
    VerificationSpecification,
    TestCase,
    VerificationType,
    VerificationReadiness,
    VerificationStatus,
    TestCaseType,
    TestExecutionStatus,
)

from app.models.project_memory import ProjectMemory
from app.models.codebase import (
    Codebase,
    CodebaseStatus,
    CodeFile,
    CodeSymbol,
    SymbolType,
    CodeDependency,
    DependencyType,
    RequirementCodeLink,
    LinkType,
)
from app.models.code_quality import (
    CodeReviewReport,
    CodeReviewFinding,
    CodeHealthStatus,
    FindingCategory,
    FindingSeverity,
)
from app.models.code_improvement import (
    CodeImprovementProposal,
    ImprovementStatus,
)
from app.models.code_improvement_evaluation import (
    CodeImprovementEvaluation,
    EvaluationResultClassification,
)
from app.models.traceability import (
    CodeTestArtifact,
    RequirementTestLink,
    TestType,
    TestRelationshipType,
)

__all__ = [
    "User",
    "UserRole",
    "RefreshToken",
    "Project",
    "ProjectStatus",
    "ProjectMemory",
    "Requirement",
    "RequirementType",
    "RequirementPriority",
    "RequirementStatus",
    "Document",
    "DocumentFileType",
    "DocumentStatus",
    "RequirementRelationship",
    "RelationshipType",
    "RequirementSuggestion",
    "SuggestionStatus",
    "RequirementImpactReport",
    "ChangeType",
    "VerificationSpecification",
    "TestCase",
    "VerificationType",
    "VerificationReadiness",
    "VerificationStatus",
    "TestCaseType",
    "TestExecutionStatus",
    "Codebase",
    "CodebaseStatus",
    "CodeFile",
    "CodeSymbol",
    "SymbolType",
    "CodeDependency",
    "DependencyType",
    "RequirementCodeLink",
    "LinkType",
    "CodeReviewReport",
    "CodeReviewFinding",
    "CodeHealthStatus",
    "FindingCategory",
    "FindingSeverity",
    "CodeImprovementProposal",
    "ImprovementStatus",
    "CodeImprovementEvaluation",
    "EvaluationResultClassification",
    "CodeTestArtifact",
    "RequirementTestLink",
    "TestType",
    "TestRelationshipType",
]
