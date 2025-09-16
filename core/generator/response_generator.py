import openai
import logging
import os
from dotenv import load_dotenv
from core.prompt_template import SYSTEM_PROMPT, SUGGESTION_FORMATTING_PROMPT_TEMPLATE
from core.error_handler import error_handler, ApiError, SystemError

load_dotenv()

class ResponseGenerator:
    """
    Generates natural language responses based on structured data.
    """

    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")


    def format_suggestions(self, suggestions: list[str]) -> str:
        """
        Uses the LLM to format the suggestions into a natural, persuasive response.
        """
        try:
            prompt = SUGGESTION_FORMATTING_PROMPT_TEMPLATE.format(suggestions)

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
            )
            return response.choices[0].message['content']
        except Exception as e:
            error = ApiError(str(e), api_name="OpenAI", context={
                "model": "gpt-4o-mini",
                "operation": "format_suggestions"
            })
            error_message = error_handler.handle_error(error)
            # Provide fallback with raw suggestions
            fallback = "I've gathered some suggestions for you, but I'm having trouble formatting them nicely. Here is the raw data:\n" + "\n".join(suggestions)
            return f"{error_message}\n\n{fallback}"

    def format_migration_report(self, report) -> str:
        """
        Formats the migration report into a user-friendly string.
        """
        return f"Migration Report:\nSuccesses: {report.successes}\nWarnings: {report.warnings}\nFailures: {report.failures}"
    
    def format_file_processing_result(self, validated_data: list, validation_result: dict, platform: str) -> str:
        """
        Format file processing results into a user-friendly message.
        
        Args:
            validated_data: List of valid campaign data
            validation_result: Validation result dictionary
            platform: Source platform name
            
        Returns:
            Formatted message string
        """
        valid_campaigns = len(validated_data)
        
        if validation_result.get("has_issues"):
            # Get total campaigns from schema comparison data
            schema_comparison = validation_result.get("schema_comparison", {})
            total_campaigns = schema_comparison.get("total_campaigns", valid_campaigns)
            failed_campaigns = total_campaigns - valid_campaigns
            
            message = f"""File processing completed with some issues:

📊 **Summary:**
- Total campaigns in file: {total_campaigns}
- Successfully validated: {valid_campaigns}
- Failed validation: {failed_campaigns}

🤖 **AI Analysis:**
{self.format_validation_analysis(schema_comparison) if schema_comparison else "Analysis not available"}

✅ **Next Steps:**
You can fix the errors based on the AI recommendations and re-upload, or proceed with migrating the {valid_campaigns} valid campaigns to Taboola."""
        else:
            message = validation_result.get("success_message", f"✅ Successfully processed all {valid_campaigns} campaigns from file")
        
        return message
    
    def format_validation_analysis(self, schema_comparison: dict) -> str:
        """
        Generate intelligent validation error analysis using LLM.
        
        Args:
            schema_comparison: Schema comparison data from SchemaValidator
            
        Returns:
            LLM-generated analysis and recommendations
        """
        try:
            analysis_prompt = self._build_validation_analysis_prompt(schema_comparison)
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_validation_system_prompt()
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
            logging.info("Validation analysis completed successfully")
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
            
            # Provide fallback analysis
            fallback_analysis = self._generate_validation_fallback(schema_comparison)
            return f"{error_message}\n\n{fallback_analysis}"

    def get_response(self, conversation_history, functions):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=conversation_history,
                functions=functions,
                function_call="auto",
            )
            return response.choices[0].message
        except Exception as e:
            error = ApiError(str(e), api_name="OpenAI", context={"model": "gpt-4o-mini"})
            error_message = error_handler.handle_error(error)
            return {"content": error_message}

    def get_response_after_function_call(self, conversation_history, response_message, function_name, content):
        """
        Calls the LLM with the result of a function call and returns the response.
        """
        try:
            updated_history = conversation_history + [response_message, {"role": "function", "name": function_name, "content": content}]
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=updated_history,
            )
            return response.choices[0].message['content']
        except Exception as e:
            error = ApiError(str(e), api_name="OpenAI", context={
                "model": "gpt-4o-mini",
                "function_name": function_name,
                "operation": "function_call_response"
            })
            return error_handler.handle_error(error)
    
    def _get_validation_system_prompt(self) -> str:
        """Get system prompt for validation analysis"""
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
    
    def _build_validation_analysis_prompt(self, schema_comparison: dict) -> str:
        """Build validation analysis prompt"""
        import json
        
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
    
    def _generate_validation_fallback(self, schema_comparison: dict) -> str:
        """Generate fallback validation analysis (when LLM is unavailable)"""
        platform = schema_comparison["platform"]
        total_issues = schema_comparison["total_issues"]
        issues = schema_comparison["validation_issues"]
        
        analysis = f"## Validation Analysis for {platform.upper()} Campaigns\n\n"
        analysis += f"Found {total_issues} validation issues that need attention.\n\n"
        
        # Group issues
        issues_by_type = {}
        for issue in issues:
            issue_type = issue["issue_type"]
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        analysis += "### Issues by Type:\n\n"
        for issue_type, type_issues in issues_by_type.items():
            analysis += f"**{issue_type.replace('_', ' ').title()}** ({len(type_issues)} issues):\n"
            for issue in type_issues[:3]:  # Only show first 3
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
