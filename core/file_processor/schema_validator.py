import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class FieldType(Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"

@dataclass
class FieldDefinition:
    """Definition of a single field schema"""
    name: str
    field_type: FieldType
    required: bool = True
    description: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    nested_schema: Optional[Dict[str, 'FieldDefinition']] = None

@dataclass
class ValidationIssue:
    """Detailed record of validation issues"""
    campaign_index: int
    field_path: str
    issue_type: str
    expected: Any
    actual: Any
    description: str

class PlatformSchema:
    """Platform-specific schema definition"""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.fields = self._load_platform_schema()
    
    def _load_platform_schema(self) -> Dict[str, FieldDefinition]:
        """Load platform-specific schema definition"""
        schema_dir = Path(__file__).parent.parent / "migration_module" / "schemas"
        schema_file = schema_dir / f"{self.platform}_validation_schema.json"
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        return self._parse_json_schema(schema_data)
    
    def _parse_json_schema(self, schema_data: Dict[str, Any]) -> Dict[str, FieldDefinition]:
        """Parse JSON schema data into FieldDefinition objects"""
        fields = {}
        
        for field_name, field_config in schema_data.items():
            field_type = FieldType(field_config.get('field_type', 'string'))
            
            # Parse nested schema
            nested_schema = None
            if field_config.get('nested_schema'):
                nested_schema = self._parse_json_schema(field_config['nested_schema'])
            
            fields[field_name] = FieldDefinition(
                name=field_name,
                field_type=field_type,
                required=field_config.get('required', True),
                description=field_config.get('description', ''),
                min_value=field_config.get('min_value'),
                max_value=field_config.get('max_value'),
                allowed_values=field_config.get('allowed_values'),
                nested_schema=nested_schema
            )
        
        return fields
    

class SchemaValidator:
    """Dynamic schema validator"""
    
    def __init__(self):
        logging.info("SchemaValidator initialized")
    
    def validate_campaigns_against_schema(self, campaigns: List[Dict[str, Any]], platform: str) -> Tuple[List[Dict[str, Any]], List[ValidationIssue]]:
        """
        Validate campaign data against schema compliance
        
        Args:
            campaigns: List of campaign data
            platform: Platform name
            
        Returns:
            Tuple of (valid_campaigns, validation_issues)
        """
        schema = PlatformSchema(platform)
        valid_campaigns = []
        all_issues = []
        
        for i, campaign in enumerate(campaigns):
            campaign_issues = self._validate_single_campaign(campaign, schema, i)
            
            if not campaign_issues:
                valid_campaigns.append(campaign)
            else:
                all_issues.extend(campaign_issues)
        
        logging.info(f"Validation complete: {len(valid_campaigns)}/{len(campaigns)} campaigns valid, {len(all_issues)} issues found")
        return valid_campaigns, all_issues
    
    def _validate_single_campaign(self, campaign: Dict[str, Any], schema: PlatformSchema, campaign_index: int) -> List[ValidationIssue]:
        """Validate single campaign"""
        issues = []
        
        # Check required fields
        for field_name, field_def in schema.fields.items():
            if field_def.required and field_name not in campaign:
                issues.append(ValidationIssue(
                    campaign_index=campaign_index,
                    field_path=field_name,
                    issue_type="missing_required_field",
                    expected=f"Required field '{field_name}'",
                    actual="Missing",
                    description=f"Missing required field: {field_name} - {field_def.description}"
                ))
                continue
            
            if field_name in campaign:
                field_issues = self._validate_field_value(
                    campaign[field_name], field_def, campaign_index, field_name
                )
                issues.extend(field_issues)
        
        # Check extra fields (fields not in schema)
        for field_name in campaign.keys():
            if field_name not in schema.fields:
                issues.append(ValidationIssue(
                    campaign_index=campaign_index,
                    field_path=field_name,
                    issue_type="unknown_field",
                    expected="Field not in schema",
                    actual=f"Field '{field_name}' with value: {campaign[field_name]}",
                    description=f"Unknown field '{field_name}' not defined in {schema.platform} schema"
                ))
        
        return issues
    
    def _validate_field_value(self, value: Any, field_def: FieldDefinition, campaign_index: int, field_path: str) -> List[ValidationIssue]:
        """Validate field value"""
        issues = []
        
        # Check data type
        if not self._check_type(value, field_def.field_type):
            issues.append(ValidationIssue(
                campaign_index=campaign_index,
                field_path=field_path,
                issue_type="type_mismatch",
                expected=f"{field_def.field_type.value}",
                actual=f"{type(value).__name__}: {value}",
                description=f"Expected {field_def.field_type.value}, got {type(value).__name__}"
            ))
            return issues  # If type error, don't proceed with further validation
        
        # Check numeric range
        if field_def.field_type in [FieldType.NUMBER, FieldType.INTEGER] and isinstance(value, (int, float)):
            if field_def.min_value is not None and value < field_def.min_value:
                issues.append(ValidationIssue(
                    campaign_index=campaign_index,
                    field_path=field_path,
                    issue_type="value_too_small",
                    expected=f">= {field_def.min_value}",
                    actual=str(value),
                    description=f"Value {value} is below minimum {field_def.min_value}"
                ))
            
            if field_def.max_value is not None and value > field_def.max_value:
                issues.append(ValidationIssue(
                    campaign_index=campaign_index,
                    field_path=field_path,
                    issue_type="value_too_large",
                    expected=f"<= {field_def.max_value}",
                    actual=str(value),
                    description=f"Value {value} exceeds maximum {field_def.max_value}"
                ))
        
        # Check allowed values
        if field_def.allowed_values and value not in field_def.allowed_values:
            issues.append(ValidationIssue(
                campaign_index=campaign_index,
                field_path=field_path,
                issue_type="invalid_value",
                expected=f"One of: {field_def.allowed_values}",
                actual=str(value),
                description=f"Value '{value}' not in allowed values: {field_def.allowed_values}"
            ))
        
        # Check if string is empty
        if field_def.field_type == FieldType.STRING and isinstance(value, str) and not value.strip():
            issues.append(ValidationIssue(
                campaign_index=campaign_index,
                field_path=field_path,
                issue_type="empty_string",
                expected="Non-empty string",
                actual="Empty string",
                description=f"Field '{field_path}' cannot be empty"
            ))
        
        # Check nested objects
        if field_def.field_type == FieldType.OBJECT and field_def.nested_schema and isinstance(value, dict):
            for nested_field, nested_def in field_def.nested_schema.items():
                if nested_field in value:
                    nested_issues = self._validate_field_value(
                        value[nested_field], nested_def, campaign_index, f"{field_path}.{nested_field}"
                    )
                    issues.extend(nested_issues)
        
        return issues
    
    def _check_type(self, value: Any, expected_type: FieldType) -> bool:
        """Check if value type matches expected type"""
        if expected_type == FieldType.STRING:
            return isinstance(value, str)
        elif expected_type == FieldType.NUMBER:
            return isinstance(value, (int, float))
        elif expected_type == FieldType.INTEGER:
            return isinstance(value, int)
        elif expected_type == FieldType.BOOLEAN:
            return isinstance(value, bool)
        elif expected_type == FieldType.OBJECT:
            return isinstance(value, dict)
        elif expected_type == FieldType.ARRAY:
            return isinstance(value, list)
        return False
    
    def generate_schema_comparison_summary(self, campaigns: List[Dict[str, Any]], issues: List[ValidationIssue], platform: str) -> Dict[str, Any]:
        """
        Generate schema comparison summary for LLM analysis
        
        Returns:
            Dictionary containing detailed comparison information
        """
        schema = PlatformSchema(platform)
        
        summary = {
            "platform": platform,
            "total_campaigns": len(campaigns),
            "total_issues": len(issues),
            "expected_schema": self._serialize_schema(schema),
            "validation_issues": [self._serialize_issue(issue) for issue in issues],
            "sample_data": campaigns[:3] if campaigns else [],  # First 3 campaigns as samples
            "issue_patterns": self._analyze_issue_patterns(issues)
        }
        
        return summary
    
    def _serialize_schema(self, schema: PlatformSchema) -> Dict[str, Any]:
        """Serialize schema definition"""
        serialized = {}
        for field_name, field_def in schema.fields.items():
            serialized[field_name] = {
                "type": field_def.field_type.value,
                "required": field_def.required,
                "description": field_def.description
            }
            if field_def.min_value is not None:
                serialized[field_name]["min_value"] = field_def.min_value
            if field_def.max_value is not None:
                serialized[field_name]["max_value"] = field_def.max_value
            if field_def.allowed_values:
                serialized[field_name]["allowed_values"] = field_def.allowed_values
        return serialized
    
    def _serialize_issue(self, issue: ValidationIssue) -> Dict[str, Any]:
        """Serialize validation issue"""
        return {
            "campaign_number": issue.campaign_index + 1,  # Start numbering from 1 for user display
            "campaign_index": issue.campaign_index,  # Keep original index for program use
            "field_path": issue.field_path,
            "issue_type": issue.issue_type,
            "expected": issue.expected,
            "actual": issue.actual,
            "description": issue.description
        }
    
    def _analyze_issue_patterns(self, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Analyze issue patterns"""
        patterns = {
            "most_common_issues": {},
            "affected_fields": {},
            "issue_types": {}
        }
        
        for issue in issues:
            # Count most common issues
            issue_key = f"{issue.field_path}:{issue.issue_type}"
            patterns["most_common_issues"][issue_key] = patterns["most_common_issues"].get(issue_key, 0) + 1
            
            # Count affected fields
            patterns["affected_fields"][issue.field_path] = patterns["affected_fields"].get(issue.field_path, 0) + 1
            
            # Count issue types
            patterns["issue_types"][issue.issue_type] = patterns["issue_types"].get(issue.issue_type, 0) + 1
        
        return patterns