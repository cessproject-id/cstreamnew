from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"status": "CStream API Running", "message": "Mode Proxy Gateway Aktif!"})

@app.route('/api/home')
def get_home():
    target_url = "https://z2.idlixku.com/"
    
    # Menggunakan Proxy Gateway publik untuk melompati blokir IP Datacenter Railway
    proxy_url = f"https://corsproxy.io/?{target_url}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print(f"[*] Mengambil data IDLIX melalui Proxy Gateway...")
        res = requests.get(proxy_url, headers=headers, timeout=15)
        print(f"[*] Status HTTP Gateway: {res.status_code}")
        
        # Jika gateway pertama gagal, coba gateway alternatif (AllOrigins)
        if res.status_code != 200:
            alt_proxy = f"https://api.allorigins.win/raw?url={target_url}"
            res = requests.get(alt_proxy, headers=headers, timeout=15)
            print(f"[*] Status HTTP Alt Gateway: {res.status_code}")
            
        if res.status_code != 200:
            return jsonify({
                "error": f"Gateway menolak dengan status {res.status_code}",
                "hero": [], "trending": [], "kdrama": [], "movies": []
            }), 200

        soup = BeautifulSoup(res.text, 'html.parser')
        
        hero, trending, kdrama, movies = [], [], [], []
        items = soup.find_all('article')
        if not items:
            items = soup.find_all('div', class_=re.compile('item|box', re.I))

        print(f"[*] Total elemen berhasil ditemukan: {len(items)}")

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
        print(f"[X] Error Critical: {str(e)}")
        return jsonify({
            "error": str(e),
            "hero": [], "trending": [], "kdrama": [], "movies": []
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
