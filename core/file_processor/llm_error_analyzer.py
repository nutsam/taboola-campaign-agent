import json
import logging
import openai
import os
from typing import Dict, List, Any
from dotenv import load_dotenv
from core.error_handler import error_handler, ApiError

load_dotenv()

class LLMErrorAnalyzer:
    """
    使用 LLM 來智能分析文件驗證錯誤並提供個性化建議
    """
    
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        logging.info("LLMErrorAnalyzer initialized")
    
    def analyze_validation_issues(self, schema_comparison: Dict[str, Any]) -> str:
        """
        使用 LLM 分析 schema 比較結果並生成智能建議
        
        Args:
            schema_comparison: SchemaValidator 生成的比較摘要
            
        Returns:
            LLM 生成的詳細分析和建議
        """
        try:
            analysis_prompt = self._build_analysis_prompt(schema_comparison)
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            analysis = response.choices[0].message['content']
            logging.info("LLM analysis completed successfully")
            return analysis
            
        except Exception as e:
            error = ApiError(
                f"Failed to analyze validation issues with LLM: {str(e)}",
                api_name="OpenAI",
                context={
                    "operation": "validation_analysis",
                    "platform": schema_comparison.get("platform"),
                    "total_issues": schema_comparison.get("total_issues")
                }
            )
            error_message = error_handler.handle_error(error)
            
            # 提供後備分析
            fallback_analysis = self._generate_fallback_analysis(schema_comparison)
            return f"{error_message}\n\n{fallback_analysis}"
    
    def _get_system_prompt(self) -> str:
        """獲取 LLM 系統提示"""
        return """You are an expert data validation specialist helping users fix campaign data upload issues. 

Your task is to analyze the differences between expected schema and actual user data, then provide clear, actionable advice.

Guidelines:
1. **Be specific**: Point out exact issues with specific campaigns and fields using campaign_number (1-based)
2. **Be helpful**: Provide concrete examples of correct data format
3. **Be encouraging**: Frame issues as easy-to-fix problems
4. **Prioritize**: Address the most critical issues first
5. **Provide examples**: Show before/after examples when possible

IMPORTANT: When referring to campaigns, always use the "campaign_number" field (which starts from 1) instead of "campaign_index" (which starts from 0). This matches what users see in their files.

Format your response with clear sections:
- 📊 Summary of Issues
- 🔧 Critical Fixes Needed  
- 💡 Recommendations
- 📝 Example Corrections

Be conversational and supportive - remember the user is trying to get their campaigns uploaded successfully."""
    
    def _build_analysis_prompt(self, schema_comparison: Dict[str, Any]) -> str:
        """構建分析提示"""
        platform = schema_comparison["platform"]
        total_campaigns = schema_comparison["total_campaigns"]
        total_issues = schema_comparison["total_issues"]
        valid_campaigns = total_campaigns - len(set(issue["campaign_index"] for issue in schema_comparison["validation_issues"]))
        
        prompt = f"""Please analyze this campaign data validation report for {platform.upper()} campaigns:

**VALIDATION SUMMARY:**
- Platform: {platform}
- Total campaigns uploaded: {total_campaigns}
- Valid campaigns: {valid_campaigns}
- Total validation issues: {total_issues}

**EXPECTED SCHEMA for {platform.upper()}:**
{json.dumps(schema_comparison["expected_schema"], indent=2)}

**VALIDATION ISSUES FOUND:**
{json.dumps(schema_comparison["validation_issues"], indent=2)}

**SAMPLE DATA (first few campaigns with their positions):**
{json.dumps(schema_comparison["sample_data"], indent=2)}

**ISSUE PATTERNS:**
{json.dumps(schema_comparison["issue_patterns"], indent=2)}

IMPORTANT CONTEXT:
- Campaign numbers in the validation issues start from 1 (user-friendly numbering)
- Campaign 1 corresponds to the first campaign in the sample data, Campaign 2 to the second, etc.
- Use "campaign_number" field when referring to specific campaigns in your response

Please provide a comprehensive analysis and actionable recommendations to help the user fix these issues. Focus on:
1. What went wrong and why (reference specific campaign numbers)
2. How to fix each type of issue
3. Specific examples showing correct format
4. Best practices to avoid similar issues

Make your response clear, friendly, and practical."""
        
        return prompt
    
    def _generate_fallback_analysis(self, schema_comparison: Dict[str, Any]) -> str:
        """生成後備分析（當 LLM 不可用時）"""
        platform = schema_comparison["platform"]
        total_issues = schema_comparison["total_issues"]
        issues = schema_comparison["validation_issues"]
        
        analysis = f"## Validation Analysis for {platform.upper()} Campaigns\n\n"
        analysis += f"Found {total_issues} validation issues that need attention.\n\n"
        
        # 分組問題
        issues_by_type = {}
        for issue in issues:
            issue_type = issue["issue_type"]
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        analysis += "### Issues by Type:\n\n"
        for issue_type, type_issues in issues_by_type.items():
            analysis += f"**{issue_type.replace('_', ' ').title()}** ({len(type_issues)} issues):\n"
            for issue in type_issues[:3]:  # 只顯示前3個
                analysis += f"- Campaign #{issue['campaign_number']}: {issue['description']}\n"
            if len(type_issues) > 3:
                analysis += f"- ... and {len(type_issues) - 3} more\n"
            analysis += "\n"
        
        analysis += "### Recommended Actions:\n"
        analysis += "1. Review the expected schema requirements\n"
        analysis += "2. Fix the issues mentioned above\n"
        analysis += "3. Re-upload your corrected file\n"
        analysis += "4. Or proceed with valid campaigns if any exist\n"
        
        return analysis
    
    def generate_quick_fix_suggestions(self, validation_issues: List[Dict[str, Any]], platform: str) -> str:
        """
        快速生成修復建議（不依賴 LLM）
        
        Args:
            validation_issues: 驗證問題列表
            platform: 平台名稱
            
        Returns:
            快速修復建議
        """
        try:
            fix_prompt = self._build_quick_fix_prompt(validation_issues, platform)
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides quick, actionable fixes for data validation issues. Be concise but specific."
                    },
                    {
                        "role": "user",
                        "content": fix_prompt
                    }
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            return response.choices[0].message['content']
            
        except Exception as e:
            logging.warning(f"LLM quick fix generation failed: {e}")
            return self._generate_simple_fixes(validation_issues, platform)
    
    def _build_quick_fix_prompt(self, validation_issues: List[Dict[str, Any]], platform: str) -> str:
        """構建快速修復提示"""
        issues_summary = {}
        for issue in validation_issues:
            key = f"{issue['field_path']}:{issue['issue_type']}"
            if key not in issues_summary:
                issues_summary[key] = {
                    "count": 0,
                    "example": issue
                }
            issues_summary[key]["count"] += 1
        
        prompt = f"Provide quick fixes for these {platform} campaign validation issues:\n\n"
        
        for key, info in issues_summary.items():
            issue = info["example"]
            count = info["count"]
            prompt += f"Issue: {issue['description']} ({count} occurrences)\n"
            prompt += f"Expected: {issue['expected']}\n"
            prompt += f"Actual: {issue['actual']}\n\n"
        
        prompt += "Provide specific, actionable fixes for each issue type."
        return prompt
    
    def _generate_simple_fixes(self, validation_issues: List[Dict[str, Any]], platform: str) -> str:
        """生成簡單的修復建議"""
        fixes = []
        
        # 分組相似的問題
        missing_fields = [i for i in validation_issues if i['issue_type'] == 'missing_required_field']
        type_mismatches = [i for i in validation_issues if i['issue_type'] == 'type_mismatch']
        value_issues = [i for i in validation_issues if 'value_too' in i['issue_type']]
        
        if missing_fields:
            field_names = list(set(i['field_path'] for i in missing_fields))
            fixes.append(f"🔧 Add missing required fields: {', '.join(field_names)}")
        
        if type_mismatches:
            fixes.append("🔧 Fix data type mismatches - ensure numbers are not in quotes")
        
        if value_issues:
            fixes.append("🔧 Check value ranges - ensure budgets are positive numbers")
        
        return "**Quick Fixes:**\n" + "\n".join(fixes) if fixes else "No specific fixes available."