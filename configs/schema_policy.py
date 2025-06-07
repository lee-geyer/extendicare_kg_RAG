"""
Pydantic schemas for metadata extraction from different document types.
Used by LlamaExtract to structure document metadata.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PolicyMeta(BaseModel):
    """Schema for extracting metadata from policy documents"""
    policy_index: Optional[str] = Field(
        None, 
        description="Policy index number (e.g., 'POL-001', 'HR-2.1')"
    )
    title: str = Field(
        ..., 
        description="Full title of the policy document"
    )
    effective_date: Optional[str] = Field(
        None, 
        description="Date when policy becomes effective (format: YYYY-MM-DD or MM/DD/YYYY)"
    )
    review_date: Optional[str] = Field(
        None, 
        description="Date when policy is scheduled for review (format: YYYY-MM-DD or MM/DD/YYYY)"
    )
    department: Optional[str] = Field(
        None, 
        description="Department or division responsible for the policy"
    )
    approved_by: Optional[str] = Field(
        None, 
        description="Name or title of person who approved the policy"
    )
    version: Optional[str] = Field(
        None, 
        description="Version number of the policy (e.g., '1.0', '2.1')"
    )


class ProcedureMeta(BaseModel):
    """Schema for extracting metadata from procedure documents"""
    procedure_index: Optional[str] = Field(
        None, 
        description="Procedure index number (e.g., 'PROC-001', 'SOP-3.2')"
    )
    title: str = Field(
        ..., 
        description="Full title of the procedure document"
    )
    effective_date: Optional[str] = Field(
        None, 
        description="Date when procedure becomes effective"
    )
    review_date: Optional[str] = Field(
        None, 
        description="Date when procedure is scheduled for review"
    )
    department: Optional[str] = Field(
        None, 
        description="Department responsible for the procedure"
    )
    related_policies: Optional[List[str]] = Field(
        None, 
        description="List of related policy indices referenced in this procedure"
    )
    risk_level: Optional[str] = Field(
        None, 
        description="Risk level associated with the procedure (High, Medium, Low)"
    )


class EducationMeta(BaseModel):
    """Schema for extracting metadata from education/training documents"""
    course_code: Optional[str] = Field(
        None, 
        description="Course or education module code"
    )
    title: str = Field(
        ..., 
        description="Full title of the education material"
    )
    duration: Optional[str] = Field(
        None, 
        description="Expected duration for completion (e.g., '2 hours', '30 minutes')"
    )
    target_audience: Optional[str] = Field(
        None, 
        description="Intended audience for the training (e.g., 'All Staff', 'Nurses', 'Management')"
    )
    competency_areas: Optional[List[str]] = Field(
        None, 
        description="List of competency areas covered by this education"
    )
    prerequisites: Optional[List[str]] = Field(
        None, 
        description="Required prerequisites before taking this training"
    )
    frequency: Optional[str] = Field(
        None, 
        description="How often this training should be completed (e.g., 'Annual', 'One-time')"
    )


class ToolMeta(BaseModel):
    """Schema for extracting metadata from tool/form documents"""
    tool_id: Optional[str] = Field(
        None, 
        description="Unique identifier for the tool or form"
    )
    title: str = Field(
        ..., 
        description="Full title of the tool or form"
    )
    tool_type: Optional[str] = Field(
        None, 
        description="Type of tool (e.g., 'Assessment Form', 'Checklist', 'Template')"
    )
    usage_context: Optional[str] = Field(
        None, 
        description="When or where this tool should be used"
    )
    related_policies: Optional[List[str]] = Field(
        None, 
        description="List of related policy indices that reference this tool"
    )
    completion_time: Optional[str] = Field(
        None, 
        description="Expected time to complete the tool"
    )


class GenericDocumentMeta(BaseModel):
    """Generic schema for documents that don't fit other categories"""
    title: str = Field(
        ..., 
        description="Title of the document"
    )
    document_type: Optional[str] = Field(
        None, 
        description="Type of document (e.g., 'Guideline', 'Manual', 'Reference')"
    )
    effective_date: Optional[str] = Field(
        None, 
        description="Date when document becomes effective"
    )
    department: Optional[str] = Field(
        None, 
        description="Department associated with the document"
    )
    keywords: Optional[List[str]] = Field(
        None, 
        description="Key terms or topics covered in the document"
    )


# Schema mapping based on document category
SCHEMA_MAPPING = {
    "policies": PolicyMeta,
    "procedures": ProcedureMeta, 
    "education": EducationMeta,
    "tools": ToolMeta,
    "forms": ToolMeta,  # Forms use the same schema as tools
    "general": GenericDocumentMeta,
}


def get_schema_for_category(category: str) -> BaseModel:
    """
    Get the appropriate Pydantic schema for a document category.
    
    Args:
        category: Document category string
        
    Returns:
        Pydantic model class for the category
    """
    category_lower = category.lower()
    return SCHEMA_MAPPING.get(category_lower, GenericDocumentMeta)