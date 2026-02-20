"""
Seed the knowledge base with publicly available Polish construction law sources.
Run once: python knowledge_base/seed_kb.py
"""
import os, requests

KNOWLEDGE_BASE_DIR = "./knowledge_base"
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

SOURCES = [
    {
        "name": "polish_construction_law_bilingual.pdf",
        "url": "https://www.ksiegarnia.beck.pl/media/product_custom_files/2/0/20127-prawo-budowlane-the-construction-law-dorota-bielecka-fragment.pdf",
        "description": "Prawo Budowlane - Polish Construction Law (bilingual EN/PL)"
    },
    {
        "name": "polish_construction_law_2022.pdf",
        "url": "https://www.warsztatarchitekta.pl/images/materialy-warsztat/2022-07-26_ustawa-z-dnia-7-lipca-2022_prawo-budowlane.pdf",
        "description": "Ustawa Prawo Budowlane 2022 - full consolidated text"
    },
]

def download_source(source):
    path = os.path.join(KNOWLEDGE_BASE_DIR, source["name"])
    if os.path.exists(path):
        print(f"  Already exists: {source['name']}")
        return
    try:
        print(f"  Downloading: {source['description']}...")
        resp = requests.get(source["url"], timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        with open(path, "wb") as f:
            f.write(resp.content)
        print(f"  Saved: {source['name']} ({len(resp.content)//1024} KB)")
    except Exception as e:
        print(f"  Failed: {source['name']} -> {e}")
        print(f"  Manual download needed from: {source['url']}")

if __name__ == "__main__":
    print("BuildIt PL - Knowledge Base Seeder")
    for source in SOURCES:
        download_source(source)
    print("Done. Now run: python ingestion/loader.py")
