import requests
from bs4 import BeautifulSoup
import json
import sys

def fetch_page(url):
    """
    指定された URL から HTML コンテンツを取得する
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
    ページのメインコンテンツから見出しや段落をもとに推奨事項データを抽出する
    ・h2 タグ: カテゴリ情報として利用 (current_category)
    ・h4 タグ: Recommendation (推奨事項タイトル)
      ※ タイトルが "Share via" のものは除外する
    ・h4 タグ直後の p タグ: Impact, ResourceType, Recommendation ID の各情報を抽出
         p タグ内は <br> タグで改行されていることを想定して分割する
    current_category が未設定の場合は、そのレコードをスキップする
    """
    soup = BeautifulSoup(html, 'html.parser')
    recommendations = []

    # ページのメインコンテンツを取得（主に article、main タグをチェック）
    content = soup.find('article')
    if not content:
        content = soup.find('main')
    if not content:
        content = soup

    current_category = ""  # h2 タグで更新されるカテゴリ
    # コンテンツ内の h2, h4, p 要素をドキュメント順にループ
    for element in content.find_all(['h2', 'h4', 'p']):
        if element.name == 'h2':
            # h2 をカテゴリ情報として利用
            current_category = element.get_text(strip=True)
        elif element.name == 'h4':
            recommendation_title = element.get_text(strip=True)
            # "Share via" は除外する（大文字小文字を区別しない）
            if recommendation_title.strip().lower() == "share via":
                continue

            details = {
                "Recommendation": recommendation_title,
                "Impact": "",
                "Category": current_category,
                "ResourceType": "",
                "RecommendationID": ""
            }
            # h4 の直後の要素から情報を抽出する
            sibling = element.find_next_sibling()
            while sibling and sibling.name not in ['h2', 'h4']:
                if sibling.name == "p":
                    text = sibling.get_text(strip=True)
                    if text.startswith("Impact:"):
                        details["Impact"] = text.replace("Impact:", "").strip()
                    if text.startswith("ResourceType:"):
                        lines = sibling.get_text(separator="\n", strip=True).split("\n")
                        for line in lines:
                            l = line.strip()
                            if l.lower().startswith("resourcetype:"):
                                details["ResourceType"] = l[len("resourcetype:"):].strip()
                            elif l.lower().startswith("recommendation id:"):
                                details["RecommendationID"] = l[len("recommendation id:"):].strip()
                sibling = sibling.find_next_sibling()
            recommendations.append(details)
    return recommendations

def save_to_json(data, filename):
    """
    抽出したデータを JSON ファイルとして保存する
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"JSON file successfully saved as {filename}")
    except IOError as e:
        print(f"Error saving JSON file: {e}", file=sys.stderr)

def main():
    url = "https://learn.microsoft.com/en-us/azure/advisor/advisor-reference-operational-excellence-recommendations"
    html = fetch_page(url)
    if not html:
        sys.exit(1)

    recommendations = parse_html(html)
    if not recommendations:
        print("No recommendations found. Exiting.", file=sys.stderr)
        sys.exit(1)

    filename = "azure_advisor_recommendations_operational-excellence.json"
    save_to_json(recommendations, filename)

if __name__ == '__main__':
    main()
