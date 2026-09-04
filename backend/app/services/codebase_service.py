"""
Codebase Service for Sprint 2.0 Code Intelligence.

Orchestrates codebase ingestion, AST analysis, symbol indexing,
dependency resolution, and Requirement ↔ Code linking with strict project isolation.
"""

from collections import Counter
import os
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.core.code_intelligence.detector import LanguageDetector
from app.core.code_intelligence.factory import CodeAnalyzerFactory
from app.core.code_intelligence.ingestion import CodebaseIngestionEngine
from app.models.user import User
from app.models.project import Project
from app.models.requirement import Requirement
from app.models.codebase import (
    Codebase,
    CodeFile,
    CodeSymbol,
    CodeDependency,
    RequirementCodeLink,
    CodebaseStatus,
    SymbolType,
    DependencyType,
    LinkType,
)
from app.repositories.codebase_repository import CodebaseRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_repository import RequirementRepository
from app.schemas.codebase import (
    CodebaseSummaryResponse,
    CodeFileSummaryResponse,
    CodeFileDetailResponse,
    CodeSymbolResponse,
    CodeDependencyResponse,
    RequirementCodeLinkCreate,
    RequirementCodeLinkResponse,
)


class CodebaseService:
    """Service layer for Codebase Intelligence."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.codebase_repo = CodebaseRepository(db)
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)

    async def _verify_project_ownership(self, user: User, project_id: UUID) -> Project:
        """Ensure the project exists and belongs to the authenticated user."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project not found.")
        if project.owner_id != user.id:
            raise ForbiddenError("You do not have permission to access this project.")
        return project

    async def ingest_zip_archive(
        self, user: User, project_id: UUID, zip_bytes: bytes, filename: str
    ) -> CodebaseSummaryResponse:
        """Extract and index a source code ZIP archive for a project."""
        await self._verify_project_ownership(user, project_id)

        # 1. Clean up existing codebase for this project to ensure fresh index
        await self.codebase_repo.delete_by_project(project_id)

        # 2. Initialize Codebase record
        repo_display_name = os.path.splitext(filename)[0] or "Project Codebase"
        codebase = Codebase(
            project_id=project_id,
            repo_name=repo_display_name,
            source_type="zip_upload",
            status=CodebaseStatus.INDEXING,
            total_files=0,
            total_lines=0,
            total_classes=0,
            total_functions=0,
            languages_summary={},
        )
        codebase = await self.codebase_repo.create(codebase)

        try:
            # 3. Securely validate & extract source files
            extracted_files = CodebaseIngestionEngine.validate_and_extract_zip(
                zip_bytes, original_filename=filename
            )

            total_lines = 0
            total_classes = 0
            total_functions = 0
            languages_counter: Counter = Counter()
            supported_count = 0
            unsupported_count = 0

            # Store created files for dependency target matching
            db_code_files: List[CodeFile] = []
            file_path_map: Dict[str, CodeFile] = {}
            parsed_results: List[Any] = []

            # 4. Analyze each file using language-specific AST analyzers
            for item in extracted_files:
                # Detect language
                det = LanguageDetector.detect(item.filename, item.content)
                languages_counter[det.language] += 1
                if det.is_supported:
                    supported_count += 1
                else:
                    unsupported_count += 1

                # AST Parse
                analyzer = CodeAnalyzerFactory.get_analyzer(det.language)
                parsed = analyzer.analyze(
                    rel_path=item.rel_path,
                    filename=item.filename,
                    content=item.content,
                    language=det.language,
                    confidence=det.confidence,
                )
                parsed_results.append(parsed)

                total_lines += parsed.line_count

                # Create CodeFile entity
                cf = CodeFile(
                    codebase_id=codebase.id,
                    project_id=project_id,
                    path=parsed.path,
                    filename=parsed.filename,
                    language=parsed.language,
                    confidence=parsed.confidence,
                    size_bytes=parsed.size_bytes,
                    line_count=parsed.line_count,
                    imports=parsed.imports,
                    exports=parsed.exports,
                    endpoints=parsed.endpoints,
                    db_interactions=parsed.db_interactions,
                    metadata_json=parsed.metadata_json,
                )
                self.db.add(cf)
                db_code_files.append(cf)
                file_path_map[parsed.path.lower()] = cf

            # Flush files to generate IDs
            await self.db.flush()

            # 5. Persist Symbols and Dependencies
            for idx, parsed in enumerate(parsed_results):
                cf = db_code_files[idx]

                # Symbols
                for sym in parsed.symbols:
                    # Map symbol type safely
                    sym_type_val = SymbolType.FUNCTION
                    for st in SymbolType:
                        if st.value == sym.symbol_type.lower():
                            sym_type_val = st
                            break

                    if sym_type_val in (SymbolType.CLASS, SymbolType.STRUCT):
                        total_classes += 1
                    elif sym_type_val in (SymbolType.FUNCTION, SymbolType.METHOD):
                        total_functions += 1

                    db_sym = CodeSymbol(
                        codebase_id=codebase.id,
                        file_id=cf.id,
                        project_id=project_id,
                        symbol_name=sym.symbol_name,
                        symbol_type=sym_type_val,
                        line_start=sym.line_start,
                        line_end=sym.line_end,
                        signature=sym.signature,
                        docstring=sym.docstring,
                        parent_symbol_name=sym.parent_symbol_name,
                        metadata_json=sym.metadata_json,
                    )
                    self.db.add(db_sym)

                # Dependencies
                for dep in parsed.dependencies:
                    # Try to resolve target_file_id
                    target_cf = None
                    clean_target = dep.target_module.replace(".", "/").lower()
                    for f_path, f_obj in file_path_map.items():
                        if clean_target in f_path:
                            target_cf = f_obj
                            break

                    dep_type_val = DependencyType.IMPORTS
                    for dt in DependencyType:
                        if dt.value == dep.dependency_type.lower():
                            dep_type_val = dt
                            break

                    db_dep = CodeDependency(
                        codebase_id=codebase.id,
                        project_id=project_id,
                        source_file_id=cf.id,
                        target_file_id=target_cf.id if target_cf else None,
                        target_module=dep.target_module,
                        dependency_type=dep_type_val,
                    )
                    self.db.add(db_dep)

            # 6. Update Codebase overview record
            codebase.status = CodebaseStatus.INDEXED
            codebase.total_files = len(extracted_files)
            codebase.total_lines = total_lines
            codebase.total_classes = total_classes
            codebase.total_functions = total_functions
            codebase.languages_summary = dict(languages_counter)
            await self.codebase_repo.update(codebase)
            await self.db.commit()

            return CodebaseSummaryResponse(
                id=codebase.id,
                project_id=codebase.project_id,
                repo_name=codebase.repo_name,
                status=codebase.status.value,
                total_files=codebase.total_files,
                total_lines=codebase.total_lines,
                total_classes=codebase.total_classes,
                total_functions=codebase.total_functions,
                languages_summary=codebase.languages_summary,
                supported_files_count=supported_count,
                unsupported_files_count=unsupported_count,
                created_at=codebase.created_at,
                updated_at=codebase.updated_at,
            )

        except Exception as e:
            codebase.status = CodebaseStatus.FAILED
            codebase.error_message = str(e)
            await self.codebase_repo.update(codebase)
            await self.db.commit()
            raise

    async def get_summary(self, user: User, project_id: UUID) -> Optional[CodebaseSummaryResponse]:
        """Fetch indexed codebase summary."""
        await self._verify_project_ownership(user, project_id)
        codebase = await self.codebase_repo.get_by_project(project_id)
        if not codebase:
            return None

        # Count supported/unsupported files
        supported_langs = LanguageDetector.SUPPORTED_LANGUAGES
        supported_count = sum(
            count for lang, count in (codebase.languages_summary or {}).items() if lang in supported_langs
        )
        unsupported_count = codebase.total_files - supported_count

        return CodebaseSummaryResponse(
            id=codebase.id,
            project_id=codebase.project_id,
            repo_name=codebase.repo_name,
            status=codebase.status.value if hasattr(codebase.status, "value") else str(codebase.status),
            total_files=codebase.total_files,
            total_lines=codebase.total_lines,
            total_classes=codebase.total_classes,
            total_functions=codebase.total_functions,
            languages_summary=codebase.languages_summary or {},
            supported_files_count=supported_count,
            unsupported_files_count=unsupported_count,
            error_message=codebase.error_message,
            created_at=codebase.created_at,
            updated_at=codebase.updated_at,
        )

    async def list_files(
        self,
        user: User,
        project_id: UUID,
        search: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[CodeFileSummaryResponse]:
        """List files in the codebase."""
        await self._verify_project_ownership(user, project_id)
        codebase = await self.codebase_repo.get_by_project(project_id)
        if not codebase:
            return []

        files = await self.codebase_repo.get_files(codebase.id, search=search, language=language)
        return [
            CodeFileSummaryResponse(
                id=f.id,
                path=f.path,
                filename=f.filename,
                language=f.language,
                confidence=f.confidence,
                size_bytes=f.size_bytes,
                line_count=f.line_count,
                symbol_count=len(f.symbols) if f.symbols else 0,
                endpoint_count=len(f.endpoints or []),
            )
            for f in files
        ]

    async def get_file_detail(
        self, user: User, project_id: UUID, file_id: UUID
    ) -> CodeFileDetailResponse:
        """Get file AST details, symbols, and endpoints."""
        await self._verify_project_ownership(user, project_id)
        code_file = await self.codebase_repo.get_file_by_id(file_id, project_id)
        if not code_file:
            raise NotFoundError("Code file not found in this project.")

        return CodeFileDetailResponse(
            id=code_file.id,
            codebase_id=code_file.codebase_id,
            project_id=code_file.project_id,
            path=code_file.path,
            filename=code_file.filename,
            language=code_file.language,
            confidence=code_file.confidence,
            size_bytes=code_file.size_bytes,
            line_count=code_file.line_count,
            imports=code_file.imports or [],
            exports=code_file.exports or [],
            endpoints=code_file.endpoints or [],
            db_interactions=code_file.db_interactions or [],
            symbols=[
                CodeSymbolResponse(
                    id=s.id,
                    file_id=s.file_id,
                    symbol_name=s.symbol_name,
                    symbol_type=s.symbol_type.value if hasattr(s.symbol_type, "value") else str(s.symbol_type),
                    line_start=s.line_start,
                    line_end=s.line_end,
                    signature=s.signature,
                    docstring=s.docstring,
                    parent_symbol_name=s.parent_symbol_name,
                    metadata_json=s.metadata_json or {},
                )
                for s in (code_file.symbols or [])
            ],
        )

    async def search_symbols(
        self,
        user: User,
        project_id: UUID,
        query: str,
        symbol_type: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 50,
    ) -> List[CodeSymbolResponse]:
        """Search code symbols by name."""
        await self._verify_project_ownership(user, project_id)
        symbols = await self.codebase_repo.search_symbols(
            project_id=project_id,
            query=query,
            symbol_type=symbol_type,
            language=language,
            limit=limit,
        )
        return [
            CodeSymbolResponse(
                id=s.id,
                file_id=s.file_id,
                symbol_name=s.symbol_name,
                symbol_type=s.symbol_type.value if hasattr(s.symbol_type, "value") else str(s.symbol_type),
                line_start=s.line_start,
                line_end=s.line_end,
                signature=s.signature,
                docstring=s.docstring,
                parent_symbol_name=s.parent_symbol_name,
                metadata_json=s.metadata_json or {},
            )
            for s in symbols
        ]

    async def get_dependencies(
        self, user: User, project_id: UUID
    ) -> List[CodeDependencyResponse]:
        """Fetch discovered dependency relationships."""
        await self._verify_project_ownership(user, project_id)
        codebase = await self.codebase_repo.get_by_project(project_id)
        if not codebase:
            return []

        deps = await self.codebase_repo.get_dependencies(codebase.id)
        return [
            CodeDependencyResponse(
                id=d.id,
                source_file_id=d.source_file_id,
                source_file_path=d.source_file.path if d.source_file else None,
                target_file_id=d.target_file_id,
                target_file_path=d.target_file.path if d.target_file else None,
                target_module=d.target_module,
                dependency_type=d.dependency_type.value if hasattr(d.dependency_type, "value") else str(d.dependency_type),
            )
            for d in deps
        ]

    async def create_link(
        self, user: User, project_id: UUID, data: RequirementCodeLinkCreate
    ) -> RequirementCodeLinkResponse:
        """Create a manual Requirement ↔ Code link."""
        await self._verify_project_ownership(user, project_id)

        # Validate requirement exists and belongs to project
        req = await self.req_repo.get_by_id(data.requirement_id)
        if not req or req.project_id != project_id:
            raise ValidationError("Requirement not found in this project.")

        # Validate file exists and belongs to project
        code_file = await self.codebase_repo.get_file_by_id(data.file_id, project_id)
        if not code_file:
            raise ValidationError("Code file not found in this project.")

        link_type_val = LinkType.EXPLICIT_MANUAL
        for lt in LinkType:
            if lt.value == data.link_type.lower():
                link_type_val = lt
                break

        link = RequirementCodeLink(
            project_id=project_id,
            requirement_id=data.requirement_id,
            file_id=data.file_id,
            symbol_id=data.symbol_id,
            link_type=link_type_val,
            notes=data.notes,
        )
        link = await self.codebase_repo.create_link(link)
        await self.db.commit()

        # Fetch created link with relationships
        links = await self.codebase_repo.get_links(project_id, data.requirement_id)
        created_link = next((l for l in links if l.id == link.id), link)

        return RequirementCodeLinkResponse(
            id=created_link.id,
            project_id=created_link.project_id,
            requirement_id=created_link.requirement_id,
            requirement_title=req.title,
            requirement_identifier=req.original_req_id or f"REQ-{str(req.id)[:6]}",
            file_id=created_link.file_id,
            file_path=code_file.path,
            file_language=code_file.language,
            symbol_id=created_link.symbol_id,
            symbol_name=created_link.symbol.symbol_name if created_link.symbol else None,
            symbol_type=created_link.symbol.symbol_type.value if created_link.symbol else None,
            link_type=created_link.link_type.value if hasattr(created_link.link_type, "value") else str(created_link.link_type),
            notes=created_link.notes,
            created_at=created_link.created_at,
        )

    async def list_links(
        self, user: User, project_id: UUID, requirement_id: Optional[UUID] = None
    ) -> List[RequirementCodeLinkResponse]:
        """List Requirement ↔ Code links for a project."""
        await self._verify_project_ownership(user, project_id)
        links = await self.codebase_repo.get_links(project_id, requirement_id)
        return [
            RequirementCodeLinkResponse(
                id=l.id,
                project_id=l.project_id,
                requirement_id=l.requirement_id,
                requirement_title=l.requirement.title if l.requirement else None,
                requirement_identifier=l.requirement.original_req_id if l.requirement else None,
                file_id=l.file_id,
                file_path=l.file.path if l.file else None,
                file_language=l.file.language if l.file else None,
                symbol_id=l.symbol_id,
                symbol_name=l.symbol.symbol_name if l.symbol else None,
                symbol_type=l.symbol.symbol_type.value if l.symbol and hasattr(l.symbol.symbol_type, "value") else (str(l.symbol.symbol_type) if l.symbol else None),
                link_type=l.link_type.value if hasattr(l.link_type, "value") else str(l.link_type),
                notes=l.notes,
                created_at=l.created_at,
            )
            for l in links
        ]

    async def delete_link(self, user: User, project_id: UUID, link_id: UUID) -> bool:
        """Delete a Requirement ↔ Code link."""
        await self._verify_project_ownership(user, project_id)
        success = await self.codebase_repo.delete_link(link_id, project_id)
        if not success:
            raise NotFoundError("Requirement code link not found.")
        await self.db.commit()
        return True

    async def delete_codebase(self, user: User, project_id: UUID) -> bool:
        """Delete codebase and reset index for project."""
        await self._verify_project_ownership(user, project_id)
        success = await self.codebase_repo.delete_by_project(project_id)
        await self.db.commit()
        return success
