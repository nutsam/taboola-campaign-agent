from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class MappingRule(BaseModel):
    source_field: Optional[str] = None
    default: Optional[Any] = None
    warning: Optional[str] = None

class PlatformSchema(BaseModel):
    name: MappingRule
    daily_cap: MappingRule
    branding_text: MappingRule
    cpc_bid: MappingRule
    creatives: MappingRule
