import json
import logging
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
    """定義單一字段的 schema"""
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
    """驗證問題的詳細記錄"""
    campaign_index: int
    field_path: str
    issue_type: str
    expected: Any
    actual: Any
    description: str

class PlatformSchema:
    """平台特定的 schema 定義"""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.fields = self._load_platform_schema()
    
    def _load_platform_schema(self) -> Dict[str, FieldDefinition]:
        """載入平台特定的 schema 定義"""
        if self.platform == 'facebook':
            return {
                'name': FieldDefinition(
                    name='name',
                    field_type=FieldType.STRING,
                    required=True,
                    description='Campaign name - must be a non-empty string'
                ),
                'objective': FieldDefinition(
                    name='objective',
                    field_type=FieldType.STRING,
                    required=True,
                    description='Campaign objective',
                    allowed_values=['LINK_CLICKS', 'CONVERSIONS', 'REACH', 'BRAND_AWARENESS']
                ),
                'daily_budget': FieldDefinition(
                    name='daily_budget',
                    field_type=FieldType.NUMBER,
                    required=True,
                    description='Daily budget in USD',
                    min_value=1.0,
                    max_value=100000.0
                ),
                'targeting': FieldDefinition(
                    name='targeting',
                    field_type=FieldType.OBJECT,
                    required=False,
                    description='Targeting configuration object',
                    nested_schema={
                        'geo': FieldDefinition('geo', FieldType.STRING, False, 'Geographic targeting'),
                        'age_min': FieldDefinition('age_min', FieldType.INTEGER, False, 'Minimum age', 13, 65),
                        'age_max': FieldDefinition('age_max', FieldType.INTEGER, False, 'Maximum age', 18, 65),
                        'interests': FieldDefinition('interests', FieldType.ARRAY, False, 'Interest targeting')
                    }
                ),
                'creatives': FieldDefinition(
                    name='creatives',
                    field_type=FieldType.ARRAY,
                    required=False,
                    description='Creative assets array'
                )
            }
        elif self.platform == 'twitter':
            return {
                'name': FieldDefinition(
                    name='name',
                    field_type=FieldType.STRING,
                    required=True,
                    description='Campaign name - must be a non-empty string'
                ),
                'total_budget': FieldDefinition(
                    name='total_budget',
                    field_type=FieldType.NUMBER,
                    required=True,
                    description='Total campaign budget in USD',
                    min_value=1.0
                ),
                'account_name': FieldDefinition(
                    name='account_name',
                    field_type=FieldType.STRING,
                    required=False,
                    description='Twitter account name'
                ),
                'tweet_creatives': FieldDefinition(
                    name='tweet_creatives',
                    field_type=FieldType.ARRAY,
                    required=False,
                    description='Tweet creative content array'
                )
            }
        else:
            return {}

class SchemaValidator:
    """動態 schema 驗證器"""
    
    def __init__(self):
        logging.info("SchemaValidator initialized")
    
    def validate_campaigns_against_schema(self, campaigns: List[Dict[str, Any]], platform: str) -> Tuple[List[Dict[str, Any]], List[ValidationIssue]]:
        """
        驗證活動數據與 schema 的符合性
        
        Args:
            campaigns: 活動數據列表
            platform: 平台名稱
            
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
        """驗證單一活動"""
        issues = []
        
        # 檢查必需字段
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
        
        # 檢查額外字段 (不在 schema 中的字段)
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
        """驗證字段值"""
        issues = []
        
        # 檢查數據類型
        if not self._check_type(value, field_def.field_type):
            issues.append(ValidationIssue(
                campaign_index=campaign_index,
                field_path=field_path,
                issue_type="type_mismatch",
                expected=f"{field_def.field_type.value}",
                actual=f"{type(value).__name__}: {value}",
                description=f"Expected {field_def.field_type.value}, got {type(value).__name__}"
            ))
            return issues  # 如果類型錯誤，不進行進一步驗證
        
        # 檢查數值範圍
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
        
        # 檢查允許的值
        if field_def.allowed_values and value not in field_def.allowed_values:
            issues.append(ValidationIssue(
                campaign_index=campaign_index,
                field_path=field_path,
                issue_type="invalid_value",
                expected=f"One of: {field_def.allowed_values}",
                actual=str(value),
                description=f"Value '{value}' not in allowed values: {field_def.allowed_values}"
            ))
        
        # 檢查字符串是否為空
        if field_def.field_type == FieldType.STRING and isinstance(value, str) and not value.strip():
            issues.append(ValidationIssue(
                campaign_index=campaign_index,
                field_path=field_path,
                issue_type="empty_string",
                expected="Non-empty string",
                actual="Empty string",
                description=f"Field '{field_path}' cannot be empty"
            ))
        
        # 檢查嵌套對象
        if field_def.field_type == FieldType.OBJECT and field_def.nested_schema and isinstance(value, dict):
            for nested_field, nested_def in field_def.nested_schema.items():
                if nested_field in value:
                    nested_issues = self._validate_field_value(
                        value[nested_field], nested_def, campaign_index, f"{field_path}.{nested_field}"
                    )
                    issues.extend(nested_issues)
        
        return issues
    
    def _check_type(self, value: Any, expected_type: FieldType) -> bool:
        """檢查值的類型是否符合預期"""
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
        生成 schema 比較摘要，用於 LLM 分析
        
        Returns:
            包含詳細比較信息的字典
        """
        schema = PlatformSchema(platform)
        
        summary = {
            "platform": platform,
            "total_campaigns": len(campaigns),
            "total_issues": len(issues),
            "expected_schema": self._serialize_schema(schema),
            "validation_issues": [self._serialize_issue(issue) for issue in issues],
            "sample_data": campaigns[:3] if campaigns else [],  # 前3個活動作為樣本
            "issue_patterns": self._analyze_issue_patterns(issues)
        }
        
        return summary
    
    def _serialize_schema(self, schema: PlatformSchema) -> Dict[str, Any]:
        """序列化 schema 定義"""
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
        """序列化驗證問題"""
        return {
            "campaign_number": issue.campaign_index + 1,  # 從 1 開始編號給用戶看
            "campaign_index": issue.campaign_index,  # 保留原始索引供程序使用
            "field_path": issue.field_path,
            "issue_type": issue.issue_type,
            "expected": issue.expected,
            "actual": issue.actual,
            "description": issue.description
        }
    
    def _analyze_issue_patterns(self, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """分析問題模式"""
        patterns = {
            "most_common_issues": {},
            "affected_fields": {},
            "issue_types": {}
        }
        
        for issue in issues:
            # 統計最常見的問題
            issue_key = f"{issue.field_path}:{issue.issue_type}"
            patterns["most_common_issues"][issue_key] = patterns["most_common_issues"].get(issue_key, 0) + 1
            
            # 統計受影響的字段
            patterns["affected_fields"][issue.field_path] = patterns["affected_fields"].get(issue.field_path, 0) + 1
            
            # 統計問題類型
            patterns["issue_types"][issue.issue_type] = patterns["issue_types"].get(issue.issue_type, 0) + 1
        
        return patterns