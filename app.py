from flask import Flask, jsonify
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"status": "CStream API Running", "message": "Backend siap beraksi!"})

@app.route('/api/home')
def get_home():
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        url = "https://z2.idlixku.com/"
        
        response = scraper.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({"error": f"IDLIX menolak dengan status {response.status_code}"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')
        
        hero, trending, kdrama, movies = [], [], [], []
        items = soup.find_all(['article', 'div'], class_=re.compile('item|post'))
        
        for item in items:
            try:
                a_tag = item.find('a')
                if not a_tag: continue
                
                link = a_tag.get('href', '')
                if not link: continue
                
                title = a_tag.get('title') or (item.find(['h2', 'h3']).text.strip() if item.find(['h2', 'h3']) else "Unknown")
                
                img = item.find('img')
                cover = ""
                if img:
                    cover = img.get('data-src') or img.get('src') or ""
                    if cover.startswith('//'): cover = 'https:' + cover
                
                if not cover: continue

                rating_tag = item.find(class_=re.compile('rating', re.I))
                rating = re.sub(r'[^\d.]', '', rating_tag.text.strip()) if rating_tag else "7.0"
                if not rating: rating = "7.0"
                
                quality_tag = item.find(class_=re.compile('quality|mvk', re.I))
                quality = quality_tag.text.strip() if quality_tag else "HD"
                
                media_type = 'series' if '/series/' in link or '/tvshows/' in link else 'movie'
                
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
                    "synopsis": "Sinopsis lengkap dimuat dari IDLIX.",
                    "vidUrl": ""
                }
                
                if len(hero) < 5:
                    hero.append(data_obj)
                elif len(trending) < 8:
                    trending.append(data_obj)
                elif media_type == 'series' and len(kdrama) < 10:
                    kdrama.append(data_obj)
                elif media_type == 'movie' and len(movies) < 10:
                    movies.append(data_obj)
            except Exception:
                continue

        # Jika hasil scraping kosong (terblokir total), berikan struktur kosong agar frontend tidak crash
        if not hero and not trending:
            return jsonify({"error": "Gagal mengekstrak elemen HTML IDLIX. Struktur situs mungkin berubah."}), 500

        return jsonify({
            "hero": hero,
            "trending": trending,
            "kdrama": kdrama,
            "movies": movies
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
