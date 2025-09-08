"""
Workflow Manager - Advanced workflow orchestration for Creator v1 (CRT4)
Manages complex multi-step content generation workflows with dependencies, conditions, and error handling
"""

import logging
import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid

from ...core.config import UmbraConfig
from .analytics import CreatorAnalytics, track_operation
from .errors import CreatorError, WorkflowError

logger = logging.getLogger(__name__)

class StepStatus(Enum):
    """Status of workflow step"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class WorkflowStatus(Enum):
    """Status of entire workflow"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    id: str
    name: str
    action: str
    params: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[int] = 300
    on_failure: str = "stop"  # "stop", "continue", "retry"
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

@dataclass
class Workflow:
    """Complete workflow definition"""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    created_at: datetime
    created_by: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.CREATED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    progress_percentage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

@dataclass
class WorkflowTemplate:
    """Reusable workflow template"""
    id: str
    name: str
    description: str
    category: str
    step_templates: List[Dict[str, Any]]
    default_params: Dict[str, Any] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)
    estimated_duration_seconds: Optional[int] = None
    tags: List[str] = field(default_factory=list)

class WorkflowManager:
    """Advanced workflow orchestration manager"""
    
    def __init__(self, config: UmbraConfig, analytics: Optional[CreatorAnalytics] = None):
        self.config = config
        self.analytics = analytics
        
        # Workflow storage
        self.workflows: Dict[str, Workflow] = {}
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.running_workflows: Set[str] = set()
        
        # Configuration
        self.max_concurrent_workflows = config.get("CREATOR_WORKFLOW_MAX_CONCURRENT", 10)
        self.default_timeout = config.get("CREATOR_WORKFLOW_DEFAULT_TIMEOUT_SECONDS", 3600)
        self.cleanup_interval = config.get("CREATOR_WORKFLOW_CLEANUP_INTERVAL_SECONDS", 300)
        
        # Task management
        self.step_executors: Dict[str, Callable] = {}
        self.conditions_evaluators: Dict[str, Callable] = {}
        
        # Initialize default templates
        self._initialize_default_templates()
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Workflow manager initialized")
    
    def _initialize_default_templates(self):
        """Initialize built-in workflow templates"""
        
        # Social Media Campaign Template
        self.templates["social_media_campaign"] = WorkflowTemplate(
            id="social_media_campaign",
            name="Social Media Campaign",
            description="Complete social media campaign with posts, images, and analytics",
            category="marketing",
            step_templates=[
                {
                    "id": "content_research",
                    "name": "Content Research",
                    "action": "research_topic",
                    "params": {"topic": "${topic}", "platform": "${platform}"}
                },
                {
                    "id": "generate_posts",
                    "name": "Generate Posts",
                    "action": "generate_content_pack",
                    "params": {"topic": "${topic}", "platform": "${platform}", "tone": "${tone}"},
                    "dependencies": ["content_research"]
                },
                {
                    "id": "generate_images",
                    "name": "Generate Images",
                    "action": "generate_image",
                    "params": {"prompt": "${image_prompt}", "count": "${image_count}"},
                    "dependencies": ["generate_posts"]
                },
                {
                    "id": "validate_content",
                    "name": "Validate Content",
                    "action": "validate_content",
                    "params": {"platform": "${platform}"},
                    "dependencies": ["generate_posts", "generate_images"]
                },
                {
                    "id": "export_bundle",
                    "name": "Export Campaign Bundle",
                    "action": "export_bundle",
                    "params": {"format": "zip"},
                    "dependencies": ["validate_content"]
                }
            ],
            required_params=["topic", "platform"],
            default_params={"tone": "professional", "image_count": 3},
            estimated_duration_seconds=300,
            tags=["social", "marketing", "campaign"]
        )
        
        # Content Localization Template
        self.templates["content_localization"] = WorkflowTemplate(
            id="content_localization",
            name="Content Localization",
            description="Localize content for multiple languages and regions",
            category="localization",
            step_templates=[
                {
                    "id": "analyze_content",
                    "name": "Analyze Source Content",
                    "action": "analyze_content",
                    "params": {"content": "${source_content}"}
                },
                {
                    "id": "translate_content",
                    "name": "Translate Content",
                    "action": "translate_content",
                    "params": {
                        "content": "${source_content}",
                        "target_languages": "${languages}",
                        "preserve_tone": True
                    },
                    "dependencies": ["analyze_content"]
                },
                {
                    "id": "adapt_cultural",
                    "name": "Cultural Adaptation",
                    "action": "adapt_cultural_context",
                    "params": {"target_regions": "${regions}"},
                    "dependencies": ["translate_content"]
                },
                {
                    "id": "validate_localized",
                    "name": "Validate Localized Content",
                    "action": "validate_localization",
                    "params": {"languages": "${languages}"},
                    "dependencies": ["adapt_cultural"]
                }
            ],
            required_params=["source_content", "languages"],
            default_params={"regions": "auto"},
            estimated_duration_seconds=600,
            tags=["localization", "translation", "cultural"]
        )
        
        # SEO Content Optimization Template
        self.templates["seo_optimization"] = WorkflowTemplate(
            id="seo_optimization",
            name="SEO Content Optimization",
            description="Optimize content for search engine visibility",
            category="seo",
            step_templates=[
                {
                    "id": "keyword_research",
                    "name": "Keyword Research",
                    "action": "seo_brief",
                    "params": {"topic": "${topic}", "target_audience": "${audience}"}
                },
                {
                    "id": "generate_seo_content",
                    "name": "Generate SEO-Optimized Content",
                    "action": "generate_seo_content",
                    "params": {
                        "topic": "${topic}",
                        "target_length": "${content_length}",
                        "focus_keywords": "${focus_keywords}"
                    },
                    "dependencies": ["keyword_research"]
                },
                {
                    "id": "generate_metadata",
                    "name": "Generate SEO Metadata",
                    "action": "seo_metadata",
                    "params": {"content_type": "${content_type}"},
                    "dependencies": ["generate_seo_content"]
                },
                {
                    "id": "optimize_structure",
                    "name": "Optimize Content Structure",
                    "action": "optimize_content_structure",
                    "params": {"format": "${output_format}"},
                    "dependencies": ["generate_seo_content"]
                }
            ],
            required_params=["topic"],
            default_params={
                "audience": "general",
                "content_length": "long",
                "content_type": "article",
                "output_format": "html"
            },
            estimated_duration_seconds=240,
            tags=["seo", "optimization", "content"]
        )
    
    async def create_workflow_from_template(self, template_id: str, params: Dict[str, Any],
                                          name: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """Create workflow instance from template"""
        try:
            if template_id not in self.templates:
                raise WorkflowError(f"Template not found: {template_id}")
            
            template = self.templates[template_id]
            
            # Validate required parameters
            missing_params = [p for p in template.required_params if p not in params]
            if missing_params:
                raise WorkflowError(f"Missing required parameters: {missing_params}")
            
            # Merge with default params
            merged_params = {**template.default_params, **params}
            
            # Create workflow steps from template
            steps = []
            for step_template in template.step_templates:
                step_params = self._substitute_parameters(step_template["params"], merged_params)
                
                step = WorkflowStep(
                    id=step_template["id"],
                    name=step_template["name"],
                    action=step_template["action"],
                    params=step_params,
                    dependencies=step_template.get("dependencies", []),
                    conditions=step_template.get("conditions", []),
                    max_retries=step_template.get("max_retries", 3),
                    timeout_seconds=step_template.get("timeout_seconds", 300),
                    on_failure=step_template.get("on_failure", "stop")
                )
                steps.append(step)
            
            # Create workflow
            workflow_id = str(uuid.uuid4())
            workflow = Workflow(
                id=workflow_id,
                name=name or f"{template.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                description=template.description,
                steps=steps,
                created_at=datetime.now(),
                created_by=user_id,
                metadata={
                    "template_id": template_id,
                    "template_params": merged_params,
                    "estimated_duration": template.estimated_duration_seconds
                }
            )
            
            self.workflows[workflow_id] = workflow
            
            logger.info(f"Created workflow {workflow_id} from template {template_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to create workflow from template {template_id}: {e}")
            raise WorkflowError(f"Workflow creation failed: {e}")
    
    async def create_custom_workflow(self, name: str, steps: List[Dict[str, Any]],
                                   description: str = "", user_id: Optional[str] = None) -> str:
        """Create custom workflow from step definitions"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Create workflow steps
            workflow_steps = []
            for i, step_def in enumerate(steps):
                step = WorkflowStep(
                    id=step_def.get("id", f"step_{i+1}"),
                    name=step_def.get("name", f"Step {i+1}"),
                    action=step_def["action"],
                    params=step_def.get("params", {}),
                    dependencies=step_def.get("dependencies", []),
                    conditions=step_def.get("conditions", []),
                    max_retries=step_def.get("max_retries", 3),
                    timeout_seconds=step_def.get("timeout_seconds", 300),
                    on_failure=step_def.get("on_failure", "stop")
                )
                workflow_steps.append(step)
            
            # Validate dependencies
            step_ids = {step.id for step in workflow_steps}
            for step in workflow_steps:
                invalid_deps = [dep for dep in step.dependencies if dep not in step_ids]
                if invalid_deps:
                    raise WorkflowError(f"Invalid dependencies in step {step.id}: {invalid_deps}")
            
            # Create workflow
            workflow = Workflow(
                id=workflow_id,
                name=name,
                description=description,
                steps=workflow_steps,
                created_at=datetime.now(),
                created_by=user_id,
                metadata={"custom_workflow": True}
            )
            
            self.workflows[workflow_id] = workflow
            
            logger.info(f"Created custom workflow {workflow_id}: {name}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to create custom workflow: {e}")
            raise WorkflowError(f"Custom workflow creation failed: {e}")
    
    async def execute_workflow(self, workflow_id: str, executor_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            raise WorkflowError(f"Workflow not found: {workflow_id}")
        
        if len(self.running_workflows) >= self.max_concurrent_workflows:
            raise WorkflowError("Maximum concurrent workflows reached")
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.CREATED:
            raise WorkflowError(f"Workflow {workflow_id} is not in executable state: {workflow.status}")
        
        try:
            self.running_workflows.add(workflow_id)
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()
            
            logger.info(f"Starting workflow execution: {workflow_id}")
            
            # Track workflow start
            if self.analytics:
                self.analytics.track_generation_start(
                    "execute_workflow",
                    metadata={
                        "workflow_id": workflow_id,
                        "workflow_name": workflow.name,
                        "step_count": len(workflow.steps)
                    }
                )
            
            # Execute workflow steps
            execution_result = await self._execute_workflow_steps(workflow, executor_context or {})
            
            # Update final status
            if execution_result["success"]:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.progress_percentage = 100.0
            else:
                workflow.status = WorkflowStatus.FAILED
            
            workflow.completed_at = datetime.now()
            workflow.total_duration_seconds = (workflow.completed_at - workflow.started_at).total_seconds()
            
            # Track completion
            if self.analytics:
                if execution_result["success"]:
                    self.analytics.track_generation_complete(
                        "execute_workflow",
                        "workflow_manager",
                        "workflow_engine",
                        workflow.total_duration_seconds * 1000,
                        metadata={"workflow_id": workflow_id}
                    )
                else:
                    self.analytics.track_generation_error(
                        "execute_workflow",
                        "workflow_manager",
                        "workflow_execution_failed",
                        workflow.total_duration_seconds * 1000 if workflow.total_duration_seconds else None,
                        metadata={"workflow_id": workflow_id, "errors": execution_result["errors"]}
                    )
            
            logger.info(f"Workflow {workflow_id} completed with status: {workflow.status}")
            
            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "success": execution_result["success"],
                "results": workflow.results,
                "errors": workflow.errors,
                "duration_seconds": workflow.total_duration_seconds,
                "steps_completed": execution_result["steps_completed"],
                "steps_total": len(workflow.steps)
            }
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(str(e))
            logger.error(f"Workflow {workflow_id} execution failed: {e}")
            raise WorkflowError(f"Workflow execution failed: {e}")
        
        finally:
            self.running_workflows.discard(workflow_id)
    
    async def _execute_workflow_steps(self, workflow: Workflow, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow steps with dependency management"""
        completed_steps = set()
        failed_steps = set()
        execution_context = {**context, "workflow_results": {}}
        
        try:
            while True:
                # Find next executable steps
                executable_steps = self._find_executable_steps(workflow, completed_steps, failed_steps)
                
                if not executable_steps:
                    # No more executable steps
                    break
                
                # Execute steps in parallel where possible
                step_tasks = []
                for step in executable_steps:
                    task = self._execute_step(workflow, step, execution_context)
                    step_tasks.append((step, task))
                
                # Wait for step completion
                for step, task in step_tasks:
                    try:
                        result = await task
                        
                        if result["success"]:
                            step.status = StepStatus.COMPLETED
                            step.result = result["data"]
                            completed_steps.add(step.id)
                            
                            # Add result to context for future steps
                            execution_context["workflow_results"][step.id] = result["data"]
                            workflow.results[step.id] = result["data"]
                            
                            logger.info(f"Step {step.id} completed successfully")
                        else:
                            step.status = StepStatus.FAILED
                            step.error = result.get("error", "Unknown error")
                            failed_steps.add(step.id)
                            workflow.errors.append(f"Step {step.id}: {step.error}")
                            
                            logger.error(f"Step {step.id} failed: {step.error}")
                            
                            # Handle failure based on step configuration
                            if step.on_failure == "stop":
                                raise WorkflowError(f"Workflow stopped due to step failure: {step.id}")
                            elif step.on_failure == "retry" and step.retry_count < step.max_retries:
                                step.retry_count += 1
                                step.status = StepStatus.PENDING
                                failed_steps.discard(step.id)
                                logger.info(f"Retrying step {step.id} (attempt {step.retry_count + 1})")
                    
                    except asyncio.TimeoutError:
                        step.status = StepStatus.FAILED
                        step.error = "Step timeout"
                        failed_steps.add(step.id)
                        workflow.errors.append(f"Step {step.id} timed out")
                        
                        if step.on_failure == "stop":
                            raise WorkflowError(f"Workflow stopped due to step timeout: {step.id}")
                
                # Update progress
                workflow.progress_percentage = (len(completed_steps) / len(workflow.steps)) * 100
            
            success = len(failed_steps) == 0
            return {
                "success": success,
                "steps_completed": len(completed_steps),
                "steps_failed": len(failed_steps),
                "errors": workflow.errors
            }
            
        except Exception as e:
            logger.error(f"Workflow step execution failed: {e}")
            return {
                "success": False,
                "steps_completed": len(completed_steps),
                "steps_failed": len(failed_steps),
                "errors": workflow.errors + [str(e)]
            }
    
    def _find_executable_steps(self, workflow: Workflow, completed: Set[str], failed: Set[str]) -> List[WorkflowStep]:
        """Find steps that can be executed based on dependencies"""
        executable = []
        
        for step in workflow.steps:
            if (step.status in [StepStatus.PENDING] and 
                step.id not in completed and 
                step.id not in failed):
                
                # Check if all dependencies are completed
                deps_completed = all(dep in completed for dep in step.dependencies)
                
                # Check conditions
                conditions_met = self._evaluate_step_conditions(step, workflow.results)
                
                if deps_completed and conditions_met:
                    executable.append(step)
        
        return executable
    
    def _evaluate_step_conditions(self, step: WorkflowStep, workflow_results: Dict[str, Any]) -> bool:
        """Evaluate step execution conditions"""
        if not step.conditions:
            return True
        
        for condition in step.conditions:
            condition_type = condition.get("type", "always")
            
            if condition_type == "always":
                continue
            elif condition_type == "result_exists":
                step_id = condition["step_id"]
                field = condition.get("field")
                if step_id not in workflow_results:
                    return False
                if field and field not in workflow_results[step_id]:
                    return False
            elif condition_type == "result_equals":
                step_id = condition["step_id"]
                field = condition["field"]
                expected_value = condition["value"]
                if (step_id not in workflow_results or 
                    workflow_results[step_id].get(field) != expected_value):
                    return False
            elif condition_type == "custom":
                # Custom condition evaluation
                evaluator_name = condition["evaluator"]
                if evaluator_name in self.conditions_evaluators:
                    if not self.conditions_evaluators[evaluator_name](condition, workflow_results):
                        return False
        
        return True
    
    async def _execute_step(self, workflow: Workflow, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual workflow step"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        try:
            # Apply timeout if specified
            if step.timeout_seconds:
                result = await asyncio.wait_for(
                    self._perform_step_action(step, context),
                    timeout=step.timeout_seconds
                )
            else:
                result = await self._perform_step_action(step, context)
            
            step.completed_at = datetime.now()
            step.duration_seconds = (step.completed_at - step.started_at).total_seconds()
            
            return {"success": True, "data": result}
            
        except asyncio.TimeoutError:
            step.completed_at = datetime.now()
            step.duration_seconds = (step.completed_at - step.started_at).total_seconds()
            return {"success": False, "error": "Step execution timeout"}
        
        except Exception as e:
            step.completed_at = datetime.now()
            step.duration_seconds = (step.completed_at - step.started_at).total_seconds()
            return {"success": False, "error": str(e)}
    
    async def _perform_step_action(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual step action"""
        action = step.action
        params = step.params
        
        # Substitute context variables in parameters
        resolved_params = self._substitute_parameters(params, context)
        
        # Execute action based on registered executors
        if action in self.step_executors:
            executor = self.step_executors[action]
            return await executor(resolved_params, context)
        else:
            # Default action mapping (placeholder)
            if action == "generate_content_pack":
                return {"content_pack": f"Generated pack for {resolved_params}"}
            elif action == "generate_image":
                return {"image_url": f"https://example.com/image_{int(time.time())}.jpg"}
            elif action == "validate_content":
                return {"validation": {"valid": True, "issues": []}}
            elif action == "export_bundle":
                return {"bundle_url": f"https://example.com/bundle_{int(time.time())}.zip"}
            else:
                return {"result": f"Executed {action} with params {resolved_params}"}
    
    def _substitute_parameters(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute variables in parameters"""
        def substitute_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                if var_name in context:
                    return context[var_name]
                elif "." in var_name:
                    # Support nested variable access like ${step_id.field}
                    parts = var_name.split(".")
                    current = context
                    for part in parts:
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            return value  # Return original if not found
                    return current
                else:
                    return value  # Return original if not found
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value
        
        return {key: substitute_value(value) for key, value in params.items()}
    
    def register_step_executor(self, action: str, executor: Callable) -> None:
        """Register step executor function"""
        self.step_executors[action] = executor
        logger.info(f"Registered step executor for action: {action}")
    
    def register_condition_evaluator(self, name: str, evaluator: Callable) -> None:
        """Register condition evaluator function"""
        self.conditions_evaluators[name] = evaluator
        logger.info(f"Registered condition evaluator: {name}")
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status and progress"""
        if workflow_id not in self.workflows:
            raise WorkflowError(f"Workflow not found: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        step_statuses = []
        for step in workflow.steps:
            step_status = {
                "id": step.id,
                "name": step.name,
                "status": step.status.value,
                "duration_seconds": step.duration_seconds,
                "error": step.error
            }
            step_statuses.append(step_status)
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress_percentage": workflow.progress_percentage,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "total_duration_seconds": workflow.total_duration_seconds,
            "steps": step_statuses,
            "results": workflow.results,
            "errors": workflow.errors
        }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel running workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.CANCELLED
            self.running_workflows.discard(workflow_id)
            
            # Cancel running steps
            for step in workflow.steps:
                if step.status == StepStatus.RUNNING:
                    step.status = StepStatus.CANCELLED
            
            logger.info(f"Workflow {workflow_id} cancelled")
            return True
        
        return False
    
    def list_workflows(self, status_filter: Optional[WorkflowStatus] = None,
                      user_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List workflows with optional filtering"""
        workflows = []
        
        for workflow in self.workflows.values():
            if status_filter and workflow.status != status_filter:
                continue
            if user_filter and workflow.created_by != user_filter:
                continue
            
            workflows.append({
                "id": workflow.id,
                "name": workflow.name,
                "status": workflow.status.value,
                "created_at": workflow.created_at.isoformat(),
                "created_by": workflow.created_by,
                "progress_percentage": workflow.progress_percentage,
                "step_count": len(workflow.steps),
                "duration_seconds": workflow.total_duration_seconds
            })
        
        return sorted(workflows, key=lambda x: x["created_at"], reverse=True)
    
    def list_templates(self, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available workflow templates"""
        templates = []
        
        for template in self.templates.values():
            if category_filter and template.category != category_filter:
                continue
            
            templates.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "required_params": template.required_params,
                "default_params": template.default_params,
                "estimated_duration_seconds": template.estimated_duration_seconds,
                "step_count": len(template.step_templates),
                "tags": template.tags
            })
        
        return templates
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get workflow manager statistics"""
        total_workflows = len(self.workflows)
        running_count = len(self.running_workflows)
        
        status_counts = {}
        for status in WorkflowStatus:
            status_counts[status.value] = sum(
                1 for w in self.workflows.values() if w.status == status
            )
        
        return {
            "total_workflows": total_workflows,
            "running_workflows": running_count,
            "available_templates": len(self.templates),
            "max_concurrent_workflows": self.max_concurrent_workflows,
            "status_distribution": status_counts,
            "registered_executors": len(self.step_executors),
            "registered_evaluators": len(self.conditions_evaluators)
        }
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old workflows"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # Remove old completed/failed workflows (keep last 100)
                completed_workflows = [
                    (w.id, w.completed_at) for w in self.workflows.values()
                    if w.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
                    and w.completed_at
                ]
                
                if len(completed_workflows) > 100:
                    completed_workflows.sort(key=lambda x: x[1])
                    to_remove = completed_workflows[:-100]  # Keep last 100
                    
                    for workflow_id, _ in to_remove:
                        del self.workflows[workflow_id]
                    
                    logger.info(f"Cleaned up {len(to_remove)} old workflows")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task failed: {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'cleanup_task') and self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()

# Workflow execution context
class WorkflowContext:
    """Context for workflow execution"""
    
    def __init__(self, creator_service=None, **kwargs):
        self.creator_service = creator_service
        self.additional_context = kwargs
    
    def get_executor_context(self) -> Dict[str, Any]:
        """Get context for step executors"""
        return {
            "creator_service": self.creator_service,
            **self.additional_context
        }

# Exception classes
class WorkflowError(CreatorError):
    """Workflow-specific error"""
    pass
