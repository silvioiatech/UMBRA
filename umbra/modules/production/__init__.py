"""
Production Module Package

Advanced n8n workflow creation and management with AI-powered assistance.
"""

from .builder import WorkflowBuilder, WorkflowConnection, WorkflowNode
from .catalog import CatalogEntry, CatalogManager, NodeInfo
from .controller import EscalationLevel, ProcessingStage, ProductionController
from .costs import BudgetLimit, CostEntry, CostManager, CostSummary
from .exporter import ExportOptions, ExportResult, WorkflowExporter
from .importer import ImportConflict, ImportDiff, ImportResult, WorkflowImporter
from .n8n_client import N8nClient, N8nCredentials
from .planner import ComplexityTier, WorkflowPlanner
from .redact import ProductionRedactor, RedactionResult, RedactionRule
from .selector import NodeMapping, NodeSelector
from .stickies import StickyNote, StickyNotesManager, StickyNotesResult
from .tester import TestExecution, TestResult, WorkflowTester
from .validator import ValidationIssue, ValidationResult, WorkflowValidator

__version__ = "0.1.0"

__all__ = [
    # Core components
    "WorkflowPlanner",
    "CatalogManager",
    "NodeSelector",
    "WorkflowBuilder",
    "ProductionController",
    "WorkflowValidator",
    "WorkflowTester",
    "WorkflowImporter",
    "WorkflowExporter",
    "StickyNotesManager",
    "ProductionRedactor",
    "CostManager",
    "N8nClient",

    # Data classes
    "ComplexityTier",
    "NodeInfo",
    "CatalogEntry",
    "NodeMapping",
    "WorkflowConnection",
    "WorkflowNode",
    "EscalationLevel",
    "ProcessingStage",
    "ValidationIssue",
    "ValidationResult",
    "TestExecution",
    "TestResult",
    "ImportConflict",
    "ImportDiff",
    "ImportResult",
    "ExportOptions",
    "ExportResult",
    "StickyNote",
    "StickyNotesResult",
    "RedactionRule",
    "RedactionResult",
    "CostEntry",
    "BudgetLimit",
    "CostSummary",
    "N8nCredentials"
]
