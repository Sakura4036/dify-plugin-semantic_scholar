from collections.abc import Generator
from typing import Any
import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class TitleSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        # Get parameters
        query = tool_parameters.get("query", "")
        fields = tool_parameters.get("fields", "title,authors,abstract,year,externalIds,url,referenceCount,citationCount,influentialCitationCount")
        
        # Additional parameters
        publication_types = tool_parameters.get("publicationTypes", None)
        open_access_pdf = tool_parameters.get("openAccessPdf", None) 
        min_citation_count = tool_parameters.get("minCitationCount", None)
        year = tool_parameters.get("year", None)
        fields_of_study = tool_parameters.get("fieldsOfStudy", None)
        
        # Validate query
        if not query:
            yield self.create_text_message("错误：'query' 参数是必需的")
            return
        
        # Set API endpoint for exact title match
        url = f"https://api.semanticscholar.org/graph/v1/paper/search/match"
        
        # Prepare parameters
        params = {
            "query": query,
            "fields": fields
        }
        
        # Add optional parameters if provided
        if publication_types:
            params["publicationTypes"] = publication_types
        if open_access_pdf is not None:
            params["openAccessPdf"] = open_access_pdf
        if min_citation_count is not None:
            params["minCitationCount"] = min_citation_count
        if year:
            params["year"] = year
        if fields_of_study:
            params["fieldsOfStudy"] = fields_of_study
            
        # Prepare headers
        headers = {}
        if "api_key" in self.runtime.credentials and self.runtime.credentials["api_key"]:
            headers["x-api-key"] = self.runtime.credentials["api_key"]
        
        # Make API request
        try:
            response = requests.get(url=url, params=params, headers=headers, timeout=10)
            
            # Handle 404 error (no match found)
            if response.status_code == 404:
                yield self.create_text_message("未找到匹配标题")
                return
                
            response.raise_for_status()
            result = response.json()
            
            # Return the result
            yield self.create_json_message(result)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                yield self.create_text_message("未找到匹配标题")
            else:
                yield self.create_text_message(f"通过标题搜索论文时出错: {str(e)}")
        except Exception as e:
            # Return error message
            yield self.create_text_message(f"通过标题搜索论文时出错: {str(e)}") 