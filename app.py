from flask import Flask, jsonify
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
# Izinkan akses dari frontend lu (misal dari hp/localhost)
CORS(app)

@app.route('/')
def index():
    return jsonify({"status": "CStream API Running", "message": "Siap menyedot IDLIX!"})

@app.route('/api/home')
def get_home():
    # Menyamar sebagai browser PC asli
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    url = "https://z2.idlixku.com/"
    
    try:
        response = scraper.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Wadah data
        hero, trending, kdrama, movies = [], [], [], []
        
        # Cari semua elemen yang membungkus film (IDLIX biasanya pakai tag <article> atau class .item)
        items = soup.find_all(['article', 'div'], class_=re.compile('item|post'))
        
        for item in items:
            a_tag = item.find('a')
            if not a_tag: continue
            
            link = a_tag.get('href', '')
            # Filter hanya link internal IDLIX
            if not link or 'idlix' not in link: continue
            
            # Ekstrak Judul
            title = a_tag.get('title') or (item.find(['h2', 'h3']).text.strip() if item.find(['h2', 'h3']) else "Unknown")
            
            # Ekstrak Gambar Cover
            img = item.find('img')
            cover = img.get('data-src') or img.get('src') or "https://via.placeholder.com/200x300" if img else "https://via.placeholder.com/200x300"
            if cover.startswith('//'): cover = 'https:' + cover
            
            # Ekstrak Rating
            rating_tag = item.find(class_=re.compile('rating', re.I))
            rating = re.sub(r'[^\d.]', '', rating_tag.text.strip()) if rating_tag else "N/A"
            if not rating: rating = "N/A"
            
            # Ekstrak Kualitas (HD/CAM/WEB-DL)
            quality_tag = item.find(class_=re.compile('quality|mvk', re.I))
            quality = quality_tag.text.strip() if quality_tag else "HD"
            
            # Tentukan Tipe (Berdasarkan URL: /movie/ atau /series/)
            media_type = 'series' if '/series/' in link or '/tvshows/' in link else 'movie'
            
            # Bentuk Objek Standar CStream
            data_obj = {
                "id": link,
                "title": title,
                "cover": cover,
                "type": media_type,
                "date": "2026", # Default (bisa lu parsing lebih dalam nanti)
                "rating": rating,
                "quality": quality,
                "genre": "Drama", # Default beranda
                "specs": f"2026 · {'1 Season' if media_type == 'series' else 'Movie'} · IDLIX",
                "synopsis": "Deskripsi lengkap akan dimuat saat masuk ke detail...",
                "vidUrl": "" # Diisi kosong dulu di beranda
            }
            
            # Distribusi Data ke 4 Kategori UI kita
            if len(hero) < 5:
                hero.append(data_obj)
            elif len(trending) < 8: # Ambil 8 untuk list Tren
                trending.append(data_obj)
            elif media_type == 'series' and len(kdrama) < 10: # 10 Series
                kdrama.append(data_obj)
            elif media_type == 'movie' and len(movies) < 10: # 10 Movie
                movies.append(data_obj)
                
        return jsonify({
            "hero": hero,
            "trending": trending,
            "kdrama": kdrama,
            "movies": movies
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Default port untuk server seperti Railway
    app.run(host='0.0.0.0', port=5000)
