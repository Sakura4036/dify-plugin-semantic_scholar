from collections.abc import Generator
from typing import Any
import requests
import json

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class MultiplePapersDetailTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        # Get parameters
        paper_ids = tool_parameters.get("paper_ids", [])
        fields = tool_parameters.get("fields", "title,authors,abstract,year,externalIds,url,referenceCount,citationCount,influentialCitationCount")
        
        # Handle different input formats
        if isinstance(paper_ids, str):
            try:
                # Try to parse as JSON if it's a string
                paper_ids = json.loads(paper_ids)
            except json.JSONDecodeError:
                # If not valid JSON, split by comma as a fallback
                paper_ids = [pid.strip() for pid in paper_ids.split(",")]
        
        # Validate paper_ids
        if not paper_ids or not isinstance(paper_ids, list):
            yield self.create_text_message("Error: 'paper_ids' must be a non-empty list of paper identifiers")
            return
        
        # Set API endpoint
        url = f"https://api.semanticscholar.org/graph/v1/paper/batch"
        
        # Prepare request payload
        data = {
            "ids": paper_ids,
            "fields": fields
        }
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json"
        }
        if "api_key" in self.runtime.credentials and self.runtime.credentials["api_key"]:
            headers["x-api-key"] = self.runtime.credentials["api_key"]
        
        # Make API request
        try:
            response = requests.post(url=url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Return the results
            yield self.create_json_message(result)
            
        except Exception as e:
            # Return error message
            yield self.create_text_message(f"Error retrieving multiple paper details: {str(e)}") 