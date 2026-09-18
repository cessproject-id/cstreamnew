from flask import Flask, jsonify
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

def get_scraper():
    return cloudscraper.create_scraper(
        browser={'browser': 'firefox', 'platform': 'windows', 'desktop': True}
    )

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }

@app.route('/')
def index():
    return jsonify({"status": "CStream API Running", "message": "Multi-Domain Scraper Active!"})

@app.route('/api/home')
def get_home():
    scraper = get_scraper()
    headers = get_headers()
    
    # Daftar domain alternatif IDLIX untuk dicoba jika yang utama 403
    target_urls = [
        "https://z2.idlixku.com/",
        "https://idlix.lock/0/",
        "https://149.18.68.27/" # IP langsung jika ada
    ]
    
    html_content = None
    success_url = ""

    for url in target_urls:
        try:
            print(f"[*] Mencoba mengakses: {url}")
            headers["Referer"] = url
            res = scraper.get(url, headers=headers, timeout=10)
            print(f"[*] Status HTTP dari {url}: {res.status_code}")
            
            if res.status_code == 200:
                html_content = res.text
                success_url = url
                break
        except Exception as e:
            print(f"[X] Gagal pada {url}: {str(e)}")
            continue

    if not html_content:
        return jsonify({
            "error": "Semua domain IDLIX diblokir (403) di server Railway.",
            "hero": [], "trending": [], "kdrama": [], "movies": []
        }), 200

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        hero, trending, kdrama, movies = [], [], [], []
        items = soup.find_all('article')
        if not items:
            items = soup.find_all('div', class_=re.compile('item|box', re.I))

        print(f"[*] Berhasil parsing dari {success_url}. Total elemen: {len(items)}")

        for item in items:
            try:
                a_tag = item.find('a')
                if not a_tag: continue
                
                link = a_tag.get('href', '')
                if not link: continue
                
                title_elem = item.find(['h2', 'h3', 'span'], class_=re.compile('title', re.I))
                title = title_elem.text.strip() if title_elem else (a_tag.get('title') or "Tanpa Judul")
                
                img = item.find('img')
                cover = ""
                if img:
                    cover = img.get('data-src') or img.get('src') or img.get('data-lazy-src') or ""
                    if cover.startswith('//'): cover = 'https:' + cover
                
                if not cover or 'placeholder' in cover: continue

                rating_tag = item.find(class_=re.compile('rating', re.I))
                rating = "7.0"
                if rating_tag:
                    cleaned_rating = re.sub(r'[^\d.]', '', rating_tag.text.strip())
                    if cleaned_rating: rating = cleaned_rating
                
                quality_tag = item.find(class_=re.compile('quality|mvk|res', re.I))
                quality = quality_tag.text.strip() if quality_tag else "HD"
                
                media_type = 'series' if '/series/' in link or '/tvshows/' in link or 'season' in link.lower() else 'movie'
                
                data_obj = {
                    "id": link,
                    "title": title,
                    "cover": cover,
                    "type": media_type,
                    "date": "2026",
                    "rating": rating,
                    "quality": quality,
                    "genre": "Drama",
                    "specs": f"2026 · {'1 Season' if media_type == 'series' else 'Movie'} · IDLIX",
                    "synopsis": "Sinopsis diambil otomatis dari IDLIX.",
                    "vidUrl": ""
                }
                
                if len(hero) < 4:
                    hero.append(data_obj)
                elif len(trending) < 8:
                    trending.append(data_obj)
                elif media_type == 'series' and len(kdrama) < 10:
                    kdrama.append(data_obj)
                elif media_type == 'movie' and len(movies) < 10:
                    movies.append(data_obj)
                    
            except Exception:
                continue

        return jsonify({
            "hero": hero,
            "trending": trending,
            "kdrama": kdrama,
            "movies": movies
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "hero": [], "trending": [], "kdrama": [], "movies": []
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
