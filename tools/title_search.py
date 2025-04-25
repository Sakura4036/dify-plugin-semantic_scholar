from collections.abc import Generator
from typing import Any
import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class TitleSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        # Get parameters
        title = tool_parameters.get("title", "")
        year = tool_parameters.get("year", None)
        fields = tool_parameters.get("fields", "title,authors,abstract,year,externalIds,url,referenceCount,citationCount,influentialCitationCount")
        
        # Validate title
        if not title:
            yield self.create_text_message("Error: 'title' is required")
            return
        
        # Set API endpoint
        url = f"https://api.semanticscholar.org/graph/v1/paper/search/title"
        
        # Prepare parameters
        params = {
            "query": title,
            "fields": fields
        }
        
        # Add year parameter if provided
        if year:
            params["year"] = year
            
        # Prepare headers
        headers = {}
        if "api_key" in self.runtime.credentials and self.runtime.credentials["api_key"]:
            headers["x-api-key"] = self.runtime.credentials["api_key"]
        
        # Make API request
        try:
            response = requests.get(url=url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Return the results
            yield self.create_json_message(result)
            
        except Exception as e:
            # Return error message
            yield self.create_text_message(f"Error searching papers by title: {str(e)}") 