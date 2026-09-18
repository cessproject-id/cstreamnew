from flask import Flask, jsonify
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"status": "CStream Scraper Active", "message": "Mode Sedot IDLIX Asli Aktif!"})

@app.route('/api/home')
def get_home():
    try:
        # Menggunakan cloudscraper dengan konfigurasi browser modern
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'android',
                'desktop': False
            }
        )
        
        url = "https://z2.idlixku.com/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Referer": "https://z2.idlixku.com/",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        response = scraper.get(url, headers=headers, timeout=15)
        
        print(f"[*] Status HTTP dari IDLIX: {response.status_code}")
        
        if response.status_code != 200:
            return jsonify({"error": f"IDLIX menolak akses. Status: {response.status_code}"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')
        
        hero, trending, kdrama, movies = [], [], [], []
        
        # IDLIX biasanya membungkus list film di dalam tag <article> atau div dengan class item
        items = soup.find_all('article')
        if not items:
            # Fallback pencarian tag div jika article tidak ditemukan
            items = soup.find_all('div', class_=re.compile('item|box', re.I))

        print(f"[*] Total elemen film/series ditemukan: {len(items)}")

        for item in items:
            try:
                a_tag = item.find('a')
                if not a_tag: continue
                
                link = a_tag.get('href', '')
                if not link: continue
                
                # Judul
                title_elem = item.find(['h2', 'h3', 'span'], class_=re.compile('title', re.I))
                title = title_elem.text.strip() if title_elem else (a_tag.get('title') or "Tanpa Judul")
                
                # Gambar Cover
                img = item.find('img')
                cover = ""
                if img:
                    cover = img.get('data-src') or img.get('src') or img.get('data-lazy-src') or ""
                    if cover.startswith('//'): 
                        cover = 'https:' + cover
                
                if not cover or 'placeholder' in cover: continue

                # Rating
                rating_tag = item.find(class_=re.compile('rating', re.I))
                rating = "7.0"
                if rating_tag:
                    cleaned_rating = re.sub(r'[^\d.]', '', rating_tag.text.strip())
                    if cleaned_rating: rating = cleaned_rating
                
                # Kualitas
                quality_tag = item.find(class_=re.compile('quality|mvk|res', re.I))
                quality = quality_tag.text.strip() if quality_tag else "HD"
                
                # Tipe Media
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
                    "synopsis": "Sinopsis diambil secara otomatis dari IDLIX.",
                    "vidUrl": ""
                }
                
                # Distribusi ke array masing-masing section
                if len(hero) < 4:
                    hero.append(data_obj)
                elif len(trending) < 8:
                    trending.append(data_obj)
                elif media_type == 'series' and len(kdrama) < 10:
                    kdrama.append(data_obj)
                elif media_type == 'movie' and len(movies) < 10:
                    movies.append(data_obj)
                    
            except Exception as inner_err:
                # Lewati item yang rusak tanpa menghentikan proses loop
                continue

        # Jika setelah di-loop ternyata kosong melompong, berarti struktur HTML berubah atau diblokir total
        if not hero and not trending:
            return jsonify({"error": "Struktur HTML IDLIX gagal di-parsing atau terhalang Cloudflare challenge."}), 500

        return jsonify({
            "hero": hero,
            "trending": trending,
            "kdrama": kdrama,
            "movies": movies
        })
        
    except Exception as e:
        print(f"[X] Error Critical di Backend: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
