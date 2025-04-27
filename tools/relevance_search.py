from collections.abc import Generator
from typing import Any
import requests
import time

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class RelevanceSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        # Get parameters
        query = tool_parameters.get("query", "")
        fields = tool_parameters.get("fields", "title,authors,abstract,year,externalIds,url,referenceCount,citationCount,influentialCitationCount")
        publication_types = tool_parameters.get("publicationTypes", None)
        open_access_pdf = tool_parameters.get("openAccessPdf", None) 
        min_citation_count = tool_parameters.get("minCitationCount", None)
        year = tool_parameters.get("year", None)
        fields_of_study = tool_parameters.get("fieldsOfStudy", None)
        max_num_results = min(int(tool_parameters.get("max_num_results", 100)), 1000)  # Default 100, max 1000
        filtered = tool_parameters.get("filtered", True)  # Filter out papers without abstract
        
        # Set base URL for search
        base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        
        # Maximum results per API call
        max_results_per_query = 100
        
        try:
            # First query to get total results and first batch
            total, data = self._query_once(
                base_url=base_url,
                query=query,
                fields=fields,
                publication_types=publication_types,
                open_access_pdf=open_access_pdf,
                min_citation_count=min_citation_count,
                year=year,
                fields_of_study=fields_of_study,
                offset=0,
                limit=min(max_results_per_query, max_num_results),
                filtered=filtered
            )
            
            if total == 0:
                yield self.create_text_message('No results found.')
                return
                
            # Calculate how many more results we need
            results = data
            remaining_results = min(max_num_results, total) - len(data)
            offset = len(data)
            
            # Continue fetching if needed
            while remaining_results > 0 and offset < max_num_results:
                # Add delay to avoid rate limiting
                time.sleep(3)  # More conservative than 15 seconds
                
                batch_size = min(remaining_results, max_results_per_query)
                _, batch_data = self._query_once(
                    base_url=base_url,
                    query=query,
                    fields=fields,
                    publication_types=publication_types,
                    open_access_pdf=open_access_pdf,
                    min_citation_count=min_citation_count,
                    year=year,
                    fields_of_study=fields_of_study,
                    offset=offset,
                    limit=batch_size,
                    filtered=filtered
                )
                
                if not batch_data:
                    break
                    
                results.extend(batch_data)
                offset += len(batch_data)
                remaining_results -= len(batch_data)
            
            # Format the final result
            final_result = {
                "total": min(total, max_num_results),
                "data": results
            }
            
            yield self.create_json_message(final_result)
            
        except Exception as e:
            yield self.create_text_message(f"Error searching papers: {str(e)}")
    
    def _query_once(
        self, 
        base_url: str,
        query: str, 
        fields: str,
        publication_types: str = None,
        open_access_pdf: bool = None,
        min_citation_count: int = None,
        year: str = None,
        fields_of_study: str = None,
        offset: int = 0, 
        limit: int = 100, 
        filtered: bool = True
    ) -> tuple[int, list]:
        """
        Execute a single query to the Semantic Scholar API
        
        Returns:
            tuple: (total count of results, list of paper data)
        """
        if limit <= 0:
            return 0, []
            
        # Build params dictionary
        params = {
            "query": query,
            "fields": fields,
            "offset": offset,
            "limit": limit
        }
        
        # Add optional parameters
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

        print(f"Querying: {params}")

        # Add API key if available
        headers = {}
        if hasattr(self, 'runtime') and hasattr(self.runtime, 'credentials'):
            if "api_key" in self.runtime.credentials and self.runtime.credentials["api_key"]:
                headers["x-api-key"] = self.runtime.credentials["api_key"]
        
        # Make request
        response = requests.get(url=base_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        if response.status_code != 200:
            return 0, []
            
        response_data = response.json()
        total = response_data.get('total', 0)
        data = []
        
        # Filter results if needed
        for paper in response_data.get('data', []):
            if not paper:
                continue
                
            # Skip papers without abstract if filtering is enabled
            if filtered and 'abstract' in fields and paper.get('abstract', None) is None:
                continue
                
            data.append(paper)
            
        return total, data 