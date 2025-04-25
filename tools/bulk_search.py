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
        queries = tool_parameters.get("queries", [])
        fields = tool_parameters.get("fields", "title,authors,abstract,year,externalIds,url,referenceCount,citationCount,influentialCitationCount")
        max_num_results = min(int(tool_parameters.get("max_num_results", 100)), 1000)  # Default 100, max 1000
        filtered = tool_parameters.get("filtered", True)  # Filter out papers without abstract
        
        # Define grammar switch for query syntax
        switch_grammar = {
            "AND": '+',
            "OR": '|',
            "NOT": '-',
        }
        
        # Handle different input formats
        if isinstance(queries, str):
            try:
                # Try to parse as JSON if it's a string
                queries = json.loads(queries)
            except json.JSONDecodeError:
                # If not valid JSON, split by comma as a fallback
                queries = [q.strip() for q in queries.split(",")]
        
        # Validate queries
        if not queries or not isinstance(queries, list):
            yield self.create_text_message("错误：'queries'必须是非空的搜索词列表")
            return
        
        # Process query syntax for each query
        processed_queries = []
        for query in queries:
            # Apply grammar transformations
            for operator, symbol in switch_grammar.items():
                # Replace operator with symbol, ensuring word boundaries
                pattern = r'\b' + re.escape(operator) + r'\b'
                query = re.sub(pattern, symbol, query)
            processed_queries.append(query)
        
        # Set API endpoint
        url = "https://api.semanticscholar.org/graph/v1/paper/batch/search"
        
        # Maximum results per API call
        max_results_per_query = 100
        
        try:
            # Prepare results container
            all_results = []
            
            # Process queries in batches to avoid overloading the API
            for i in range(0, len(processed_queries), 10):  # Process 10 queries at a time
                batch_queries = processed_queries[i:i+10]
                
                # Prepare request payload for first batch
                data = {
                    "queries": batch_queries,
                    "fields": fields,
                    "offset": 0,
                    "limit": min(max_results_per_query, max_num_results)
                }
                
                # Make first API request for this batch
                batch_results = self._query_batch(url, data, filtered)
                
                # For each query that has more results, paginate if needed
                for query_idx, query_result in enumerate(batch_results):
                    total = query_result.get('total', 0)
                    query_data = query_result.get('data', [])
                    
                    # Calculate how many more results we need
                    remaining_results = min(max_num_results, total) - len(query_data)
                    offset = len(query_data)
                    
                    # Continue fetching if needed
                    while remaining_results > 0 and offset < max_num_results:
                        # Add delay to avoid rate limiting
                        time.sleep(1)
                        
                        batch_size = min(remaining_results, max_results_per_query)
                        
                        # Prepare request for next page
                        next_data = {
                            "queries": [batch_queries[query_idx]],  # Just the single query
                            "fields": fields,
                            "offset": offset,
                            "limit": batch_size
                        }
                        
                        # Request next page
                        next_results = self._query_batch(url, next_data, filtered)
                        if not next_results or not next_results[0].get('data'):
                            break
                            
                        # Add new results
                        new_data = next_results[0].get('data', [])
                        query_result['data'].extend(new_data)
                        
                        # Update counters
                        offset += len(new_data)
                        remaining_results -= len(new_data)
                    
                    # Update total to reflect actual number of results retrieved
                    query_result['total'] = min(total, max_num_results)
                
                # Add this batch's results to the overall results
                all_results.extend(batch_results)
                
                # Add delay between batches to avoid rate limiting
                if i + 10 < len(processed_queries):
                    time.sleep(2)
            
            # Return the aggregated results
            yield self.create_json_message(all_results)
            
        except Exception as e:
            # Return error message
            yield self.create_text_message(f"批量搜索出错：{str(e)}")
    
    def _query_batch(self, url: str, data: dict, filtered: bool = True) -> list:
        """
        Execute a batch query to the Semantic Scholar API
        
        Args:
            url: API endpoint URL
            data: Request payload
            filtered: Whether to filter results
            
        Returns:
            list: Search results for each query
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
            return []
            
        response_data = response.json()
        
        # Filter results if needed
        if filtered:
            for query_result in response_data:
                if 'data' in query_result and query_result['data']:
                    fields_list = data.get('fields', '').split(',')
                    filtered_data = []
                    
                    for paper in query_result['data']:
                        if not paper:
                            continue
                            
                        # Skip papers without abstract if filtering is enabled
                        if 'abstract' in fields_list and paper.get('abstract', None) is None:
                            continue
                            
                        filtered_data.append(paper)
                        
                    query_result['data'] = filtered_data
        
        return response_data 