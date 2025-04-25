from collections.abc import Generator
from typing import Any
import requests
import json
import time
import re

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class BulkSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        # Get parameters
        query = tool_parameters.get("query", "")
        fields = tool_parameters.get("fields", "title,authors,abstract,year,externalIds,url,referenceCount,citationCount,influentialCitationCount")
        max_num_results = min(int(tool_parameters.get("max_num_results", 10)), 10000)  # Default 10, max 10000
        filtered = tool_parameters.get("filtered", True)  # Filter out papers without abstract
        
        # Define grammar switch for query syntax
        switch_grammar = {
            "AND": '+',
            "OR": '|',
            "NOT": '-',
        }
        
        # Process query syntax
        if query:
            for operator, symbol in switch_grammar.items():
                # Replace operator with symbol, ensuring word boundaries
                pattern = r'\b' + re.escape(operator) + r'\b'
                query = re.sub(pattern, symbol, query)
        
        # Set API endpoint
        url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
        
        try:
            # Prepare results container
            all_papers = []
            continuation_token = None
            batch_count = 0
            total = 0
            
            # Keep fetching until we have enough results or no more are available
            while len(all_papers) < max_num_results and (batch_count == 0 or continuation_token):
                # Add delay between requests to avoid rate limiting
                if batch_count > 0:
                    time.sleep(1)
                
                # Prepare request payload
                data = {
                    "query": query,
                    "fields": fields,
                    "limit": min(1000, max_num_results - len(all_papers))
                }
                
                # Add continuation token if available
                if continuation_token:
                    data["token"] = continuation_token
                
                # Make API request
                response = self._query_batch(url, data)
                
                if not response:
                    break
                
                # Extract data from response
                batch_total = response.get("total", 0)
                if batch_count == 0:
                    total = batch_total
                
                batch_papers = response.get("data", [])
                continuation_token = response.get("token")
                
                # Filter results if needed
                if filtered and 'abstract' in fields:
                    batch_papers = [paper for paper in batch_papers if paper and paper.get('abstract', None) is not None]
                
                # Add to results
                all_papers.extend(batch_papers)
                batch_count += 1
                
                # Break if no continuation token or we've reached the limit
                if not continuation_token or len(all_papers) >= max_num_results:
                    break
            
            # Format the final result with actual number of results retrieved
            final_result = {
                "total": min(total, max_num_results),
                "data": all_papers[:max_num_results]
            }
            
            yield self.create_json_message(final_result)
            
        except Exception as e:
            # Return error message
            yield self.create_text_message(f"批量搜索出错：{str(e)}")
    
    def _query_batch(self, url: str, data: dict) -> dict:
        """
        Execute a bulk search query to the Semantic Scholar API
        
        Args:
            url: API endpoint URL
            data: Request payload
            
        Returns:
            dict: Search results including papers and continuation token
        """
        # Prepare headers
        headers = {
            "Content-Type": "application/json"
        }
        if hasattr(self, 'runtime') and hasattr(self.runtime, 'credentials'):
            if "api_key" in self.runtime.credentials and self.runtime.credentials["api_key"]:
                headers["x-api-key"] = self.runtime.credentials["api_key"]
        
        # Make request
        response = requests.post(url=url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        if response.status_code != 200:
            return {}
            
        return response.json() 