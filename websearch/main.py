from fastmcp import FastMCP
from typing import Optional
from ddgs import DDGS
import logging
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("web-search")

@mcp.tool()
def web_search(
    query: str, 
    num_results: int = 10, 
    region: str = "wt-wt", 
    safesearch: str = "moderate", 
    timelimit: Optional[str] = None
) -> dict:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: The search query string
        num_results: Number of results to return (default: 10)
        region: Region for search results (default: "wt-wt" for worldwide)
        safesearch: Safe search level - "on", "moderate", or "off" (default: "moderate")
        timelimit: Time limit for results - "d" (day), "w" (week), "m" (month), "y" (year)
    
    Returns:
        Dictionary with search results or error message
    """
    logger.info(f"?? web_search called with query: '{query}', num_results: {num_results}")
    
    try:
        # Create DDGS instance and perform search
        with DDGS() as ddgs:
            logger.info("?? Calling DuckDuckGo API...")
            
            # Force execution with list() and handle empty results
            results = list(ddgs.text(
                query, 
                max_results=num_results,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit
            ))
            
            logger.info(f"? Got {len(results)} results from DuckDuckGo")
            
            if not results:
                logger.warning("?? No results returned from DuckDuckGo")
                return {
                    "results": [],
                    "message": "No results found for this query"
                }
            
            # Format results
            formatted_results = []
            for idx, r in enumerate(results):
                formatted_results.append({
                    "title": r.get("title", "No title"),
                    "body": r.get("body", "No description"),
                    "url": r.get("href", "No URL")
                })
                logger.debug(f"  Result {idx + 1}: {r.get('title', 'N/A')}")
            
            logger.info(f"?? Returning {len(formatted_results)} formatted results")
            return {
                "results": formatted_results,
                "count": len(formatted_results)
            }
            
    except Exception as e:
        error_msg = f"Error in web_search: {str(e)}"
        logger.error(f"? {error_msg}")
        return {
            "error": error_msg,
            "results": []
        }


@mcp.tool()
def get_page_content(url: str, timeout: int = 10) -> dict:
    """
    Fetch and extract text content from a webpage.
    
    Args:
        url: The URL of the webpage to fetch
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        Dictionary with page title, text content, or error message
    """
    logger.info(f"?? get_page_content called for URL: {url}")
    
    try:
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info("?? Fetching webpage...")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        logger.info(f"? Page fetched successfully (status: {response.status_code})")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get title
        title = soup.title.string if soup.title else "No title"
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = '\n'.join(lines)
        
        # Truncate if too long (keep first 5000 characters)
        if len(content) > 5000:
            content = content[:5000] + "\n\n[Content truncated...]"
        
        logger.info(f"?? Extracted {len(content)} characters from page")
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "length": len(content)
        }
        
    except requests.Timeout:
        error_msg = f"Request timed out after {timeout} seconds"
        logger.error(f"?? {error_msg}")
        return {"error": error_msg, "url": url}
        
    except requests.RequestException as e:
        error_msg = f"Error fetching page: {str(e)}"
        logger.error(f"? {error_msg}")
        return {"error": error_msg, "url": url}
        
    except Exception as e:
        error_msg = f"Error parsing page: {str(e)}"
        logger.error(f"? {error_msg}")
        return {"error": error_msg, "url": url}


# Run the MCP server
if __name__ == "__main__":
    logger.info("?? Starting web-search MCP server...")
    mcp.run()