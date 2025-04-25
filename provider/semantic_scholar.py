from typing import Any

import requests
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class SemanticScholarProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        # Check if API key exists (optional for Semantic Scholar)
        api_key = credentials.get("api_key", "")
        
        # Test the API with a simple request
        try:
            headers = {}
            if api_key:
                headers["x-api-key"] = api_key
                
            # Try a simple request to verify the API connectivity
            response = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
