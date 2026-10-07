"""Domain models for automated engineering reports and audit certificates."""

from typing import Optional
from pydantic import BaseModel, Field


class ReportConfig(BaseModel):
    """Configuration for LaTeX / PDF validation report generation."""

    author: str = Field(default="Controls Validation Team", description="Lead validation engineer name")
    organization: str = Field(default="Wind Turbine Engineering Division", description="Issuing organization")
    turbine_model: str = Field(default="WT-5.0MW-126 (IEC Class IB)", description="Turbine model identifier")
    standard: str = Field(default="IEC 61400-1 ed.4 / GL Guideline 2010", description="Certification benchmark")
    notes: Optional[str] = Field(default=None, description="Additional engineering notes or remarks")


class ReportMetadata(BaseModel):
    """Metadata regarding a generated certification document."""

    report_id: str
    run_id: str
    dataset_name: str
    created_at: str
    tex_path: str
    pdf_path: Optional[str] = None
    pdf_generated: bool = False
    engine_used: str = "latex_jinja2"
