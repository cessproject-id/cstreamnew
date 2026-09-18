from flask import Flask, jsonify
from flask_cors import CORS
from curl_cffi import requests as c_requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"status": "CStream Scraper Active", "message": "Mode curl_cffi anti-403 aktif!"})

@app.route('/api/home')
def get_home():
    url = "https://z2.idlixku.com/"
    
    try:
        # Menggunakan curl_cffi untuk meniru TLS fingerprint browser Chrome asli (bypass Cloudflare 403)
        response = c_requests.get(url, impersonate="chrome120", timeout=20)
        
        print(f"[*] Status HTTP dari IDLIX via curl_cffi: {response.status_code}")
        
        if response.status_code != 200:
            return jsonify({"error": f"Masih diblokir dengan status {response.status_code}"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')
        
        hero, trending, kdrama, movies = [], [], []
        items = soup.find_all('article')
        if not items:
            items = soup.find_all('div', class_=re.compile('item|box', re.I))

        print(f"[*] Total elemen ditemukan: {len(items)}")

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

        if not hero and not trending:
            return jsonify({"error": "Berhasil terhubung tapi gagal parsing elemen HTML."}), 500

        return jsonify({
            "hero": hero,
            "trending": trending,
            "kdrama": kdrama,
            "movies": movies
        })
        
    except Exception as e:
        print(f"[X] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
