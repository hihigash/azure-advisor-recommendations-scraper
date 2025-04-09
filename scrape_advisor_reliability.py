import requests
from bs4 import BeautifulSoup
import json
import sys

def fetch_page(url):
    """
    Fetch HTML content from the specified URL
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}", file=sys.stderr)
        return None

def parse_html(html):
    """
    Extract recommendation data from the page's main content based on headings and paragraphs
    - h2 tags: Used as category information (current_category)
    - h4 tags: Recommendation title (excluding titles like "Share via")
    - p tags after h4: Extract Impact, ResourceType, and Recommendation ID
      Assuming p tags contain content separated by <br> tags
    Skip records where current_category is not set
    """
    soup = BeautifulSoup(html, 'html5lib')
    recommendations = []

    # Get the main content of the page (checking article, main tags)
    content = soup.find('article') or soup.find('main') or soup

    current_category = ""  # Category updated by h2 tags
    for element in content.find_all(['h2', 'h4']):
        if element.name == 'h2':
            current_category = element.get_text(strip=True)
        elif element.name == 'h4':
            recommendation_title = element.get_text(strip=True)
            if recommendation_title.strip().lower() == "share via":
                continue

            id = element.get('id')
            base_url = "https://learn.microsoft.com/en-us/azure/advisor/advisor-reference-reliability-recommendations"
            url = f"{base_url}#{id}" if id else ""

            # Use empty string if URL is not found
            details = {
                "Recommendation": recommendation_title,
                "Impact": "",
                "Category": current_category,
                "ResourceType": "",
                "RecommendationID": "",
                "Url": url
            }
            
            # Extract information from elements after h4
            sibling = element.find_next_sibling()
            while sibling and sibling.name not in ['h2', 'h4']:
                if sibling.name == "p":
                    text = sibling.get_text(strip=True)
                    if text.startswith("Impact:"):
                        details["Impact"] = text.replace("Impact:", "").strip()
                    
                    lines = sibling.get_text(separator="\n", strip=True).split("\n")
                    for line in lines:
                        l = line.strip().lower()
                        if l.startswith("resourcetype:"):
                            details["ResourceType"] = line[len("resourcetype:"):].strip()
                        elif l.startswith("recommendation id:"):
                            details["RecommendationID"] = line[len("recommendation id:"):].strip()
                
                sibling = sibling.find_next_sibling()
            
            recommendations.append(details)
    
    return recommendations

def save_to_json(data, filename):
    """
    Save extracted data as a JSON file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"JSON file successfully saved as {filename}")
    except IOError as e:
        print(f"Error saving JSON file: {e}", file=sys.stderr)

def main():
    url = "https://learn.microsoft.com/en-us/azure/advisor/advisor-reference-reliability-recommendations"
    html = fetch_page(url)
    if not html:
        sys.exit(1)

    recommendations = parse_html(html)
    if not recommendations:
        print("No recommendations found. Exiting.", file=sys.stderr)
        sys.exit(1)

    filename = "azure_advisor_reliability_recommendations.json"
    save_to_json(recommendations, filename)

if __name__ == '__main__':
    main()
