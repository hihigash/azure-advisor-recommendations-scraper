import requests
from bs4 import BeautifulSoup
import json

# ページの URL（英語版・日本語版）
url_en = "https://learn.microsoft.com/en-us/azure/advisor/advisor-reference-operational-excellence-recommendations"
url_ja = "https://learn.microsoft.com/ja-jp/azure/advisor/advisor-reference-operational-excellence-recommendations"

# 各ページを取得（エンコーディングを明示的に指定）
response_en = requests.get(url_en)
response_en.encoding = 'utf-8'
response_ja = requests.get(url_ja)
response_ja.encoding = 'utf-8'

# BeautifulSoup でパース
soup_en = BeautifulSoup(response_en.text, "html.parser")
soup_ja = BeautifulSoup(response_ja.text, "html.parser")

# 結果を格納するリスト
services = []

# ※仮定：サービス名は <h2> タグ、推奨事項は <h3> タグに記載されている
for service_en in soup_en.find_all("h2"):
    service_name_en = service_en.get_text(strip=True)
    
    # 英語版のサービスに id があれば、それをキーに日本語版を探す
    service_id = service_en.get("id")
    if service_id:
        service_ja_heading = soup_ja.find("h2", id=service_id)
        service_name_ja = service_ja_heading.get_text(strip=True) if service_ja_heading else service_name_en
    else:
        service_name_ja = service_name_en  # id がない場合は同じ名前とする

    recommendations = []
    
    # サービス見出しの直後から次の <h2> までが当該サービスの推奨事項と仮定
    sibling = service_en.find_next_sibling()
    while sibling and sibling.name != "h2":
        if sibling.name == "h3":
            # 英語版の推奨事項
            rec_id = sibling.get("id")
            rec_en_name = sibling.get_text(strip=True)
            rec_permalink_en = f"{url_en}#{rec_id}" if rec_id else None

            # 日本語版の対応する推奨事項を id で探す
            rec_ja_heading = soup_ja.find("h3", id=rec_id) if rec_id else None
            rec_ja_name = rec_ja_heading.get_text(strip=True) if rec_ja_heading else rec_en_name
            rec_permalink_ja = f"{url_ja}#{rec_id}" if rec_id else None

            recommendations.append({
                "recommendation_en": rec_en_name,
                "recommendation_permalink_en": rec_permalink_en,
                "recommendation_ja": rec_ja_name,
                "recommendation_permalink_ja": rec_permalink_ja
            })
        sibling = sibling.find_next_sibling()

    services.append({
        "service_en": service_name_en,
        "service_ja": service_name_ja,
        "recommendations": recommendations
    })

# JSON に変換して出力
with open("OperationalExcellence.json", "w", encoding="utf-8") as f:
    json.dump(services, f, ensure_ascii=False, indent=2)
