"""
Requirement -> Test Traceability Engine for Sprint 2.4.

Establishes evidence-backed links between Requirements and discovered Test Artifacts
using explicit ID matching, code symbol links, and keyword heuristics.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from app.models.requirement import Requirement
from app.models.codebase import RequirementCodeLink, CodeFile
from app.models.traceability import CodeTestArtifact, TestRelationshipType


class RequirementTestTraceabilityEngine:
    """Engine matching Requirements to Code Test Artifacts."""

    @staticmethod
    def match_requirements_to_tests(
        requirements: List[Requirement],
        test_artifacts: List[CodeTestArtifact],
        code_links: List[RequirementCodeLink],
        code_files: List[CodeFile],
    ) -> List[Dict[str, Any]]:
        """Analyzes relationships between requirements and discovered tests."""
        matched_links: List[Dict[str, Any]] = []

        code_file_map = {cf.id: cf for cf in code_files}
        # Build map of requirement_id -> list of linked code file paths
        req_code_paths: Dict[str, List[str]] = {}
        for link in code_links:
            req_id_str = str(link.requirement_id)
            if req_id_str not in req_code_paths:
                req_code_paths[req_id_str] = []
            link_file_id = getattr(link, "file_id", None) or getattr(link, "code_file_id", None)
            if link_file_id and link_file_id in code_file_map:
                req_code_paths[req_id_str].append(code_file_map[link_file_id].path)

        for req in requirements:
            req_id_str = str(req.id)
            orig_id = (req.original_req_id or "").upper()
            req_title_lower = (req.title or "").lower()
            linked_paths = req_code_paths.get(req_id_str, [])

            for test in test_artifacts:
                test_name_upper = (test.test_name or "").upper()
                test_path_lower = (test.file_path or "").lower()

                # Signal 1: Explicit Requirement ID match (DIRECT, confidence 1.0)
                if orig_id and (orig_id in test_name_upper or orig_id.replace("-", "_") in test_name_upper or orig_id in test_path_lower.upper()):
                    matched_links.append(
                        RequirementTestTraceabilityEngine._build_link_dict(
                            requirement=req,
                            test=test,
                            rel_type=TestRelationshipType.DIRECT.value,
                            confidence=1.0,
                            evidence={
                                "signal": "EXPLICIT_ID_MATCH",
                                "matched_id": orig_id,
                                "matched_in": "test_name_or_file_path",
                                "explanation": f"Explicit requirement identifier '{orig_id}' found in test '{test.test_name}'.",
                            },
                        )
                    )
                    continue

                # Signal 2: Linked Code File -> Test File Match (INFERRED, confidence 0.85)
                code_matched_path = None
                for c_path in linked_paths:
                    base_name = c_path.split("/")[-1].split(".")[0].lower()
                    if base_name and (base_name in test_path_lower or base_name in test_name_upper.lower()):
                        code_matched_path = c_path
                        break

                if code_matched_path:
                    matched_links.append(
                        RequirementTestTraceabilityEngine._build_link_dict(
                            requirement=req,
                            test=test,
                            rel_type=TestRelationshipType.INFERRED.value,
                            confidence=0.85,
                            evidence={
                                "signal": "LINKED_CODE_TEST_MATCH",
                                "linked_code_file": code_matched_path,
                                "test_file": test.file_path,
                                "explanation": f"Test '{test.file_path}' verifies code file '{code_matched_path}' which is linked to requirement '{req.title}'.",
                            },
                        )
                    )
                    continue

                # Signal 3: Title Keyword Match (INFERRED, confidence 0.70)
                req_words = [w for w in re.findall(r"\w+", req_title_lower) if len(w) > 3 and w not in ["shall", "system", "allow", "user", "with"]]
                matched_words = [w for w in req_words if w in test_name_upper.lower() or w in test_path_lower]

                if len(matched_words) >= 2 or (len(req_words) == 1 and len(matched_words) == 1):
                    matched_links.append(
                        RequirementTestTraceabilityEngine._build_link_dict(
                            requirement=req,
                            test=test,
                            rel_type=TestRelationshipType.INFERRED.value,
                            confidence=0.70,
                            evidence={
                                "signal": "KEYWORD_MATCH",
                                "matched_keywords": matched_words,
                                "explanation": f"Test name/path matched domain keywords {matched_words} from requirement title '{req.title}'.",
                            },
                        )
                    )

        return matched_links

    @staticmethod
    def _build_link_dict(
        requirement: Requirement,
        test: CodeTestArtifact,
        rel_type: str,
        confidence: float,
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "requirement_id": requirement.id,
            "test_artifact_id": test.id,
            "relationship_type": rel_type,
            "confidence": confidence,
            "evidence": evidence,
            "verified": rel_type == TestRelationshipType.DIRECT.value,
        }
