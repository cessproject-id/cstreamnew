from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({"status": "CStream API Running", "message": "Scraper IDLIX Modern Aktif!"})

@app.route('/api/home')
def get_home():
    target_url = "https://z2.idlixku.com/"
    
    # Mempertahankan Proxy Gateway yang terbukti tembus 200 di log Railway lu
    proxy_url = f"https://api.allorigins.win/raw?url={target_url}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    try:
        print("[*] Mengambil data IDLIX dengan struktur Tailwind Modern...")
        res = requests.get(proxy_url, headers=headers, timeout=20)
        
        if res.status_code != 200:
            return jsonify({
                "error": f"Gateway error: {res.status_code}",
                "hero": [], "trending": [], "kdrama": [], "movies": []
            }), 200

        soup = BeautifulSoup(res.text, 'html.parser')
        
        hero, trending, kdrama, movies = [], [], [], []
        seen_ids = set() # Untuk mencegah film yang sama masuk dua kali
        
        # 1. PARSING HERO BANNER SEHALUS MUNGKIN
        hero_container = soup.find('div', class_=re.compile('absolute inset-0'))
        if hero_container:
            hero_img = hero_container.find('img', class_=re.compile('hero-fade-in'))
            if hero_img:
                hero.append({
                    "id": "/movie/the-end-of-oak-street-2026", # Default fallback
                    "title": hero_img.get('alt', 'Pilihan Hari Ini'),
                    "cover": hero_img.get('src', ''),
                    "type": "movie",
                    "date": "2026",
                    "rating": "8.5",
                    "quality": "HD",
                    "genre": "Trending",
                    "specs": "2026 · Movie · Spesial",
                    "synopsis": "Tonton rilis eksklusif pilihan hari ini.",
                    "vidUrl": ""
                })

        # 2. PARSING SEMUA SECTION (Trending, Drama, Movies)
        sections = soup.find_all('section')
        for sec in sections:
            # Cari judul section (misal: "Korean Drama", "Film Terbaru")
            header_tag = sec.find('h2')
            section_title = header_tag.text.lower() if header_tag else ""
            
            cards = sec.find_all('div', class_=re.compile('content-card'))
            for card in cards:
                try:
                    a_tag = card.find('a')
                    if not a_tag: continue
                    link = a_tag.get('href', '')
                    if not link: continue
                    
                    # Tambahkan domain jika linknya relatif (/series/...)
                    full_link = f"https://z2.idlixku.com{link}" if link.startswith('/') else link
                    
                    # Judul
                    title_tag = card.find('h3')
                    title = title_tag.text.strip() if title_tag else "Tanpa Judul"
                    
                    # Cover
                    img_tag = card.find('img')
                    cover = img_tag.get('src', '') if img_tag else ""
                    if not cover or 'placeholder' in cover.lower(): continue
                    
                    # Kualitas / Label (WEB-DL, S1, S7, dsb)
                    badge_tag = card.find('span', class_=re.compile('content-badge'))
                    quality = badge_tag.text.strip() if badge_tag else "HD"
                    
                    # Rating
                    rating_tag = card.find('span', class_=re.compile('text-accent-gold'))
                    rating = rating_tag.text.strip() if rating_tag else "7.0"
                    
                    media_type = 'series' if '/series/' in link else 'movie'
                    
                    data_obj = {
                        "id": full_link,
                        "title": title,
                        "cover": cover,
                        "type": media_type,
                        "date": "2026",
                        "rating": rating,
                        "quality": quality,
                        "genre": "K-Drama" if "korean" in section_title else "Film",
                        "specs": f"2026 · {'Series' if media_type == 'series' else 'Movie'} · IDLIX",
                        "synopsis": "Informasi sinopsis tersedia di halaman pemutar.",
                        "vidUrl": ""
                    }
                    
                    # Hindari duplikat film yang sama muncul di dua kategori
                    if link in seen_ids: continue
                    seen_ids.add(link)

                    # LOGIKA PEMBAGIAN KATEGORI
                    # Jika card memiliki elemen angka rank besar (1, 2, 3) -> Masuk Trending
                    if card.find('span', class_=re.compile('text-2xl|text-3xl')):
                        if len(trending) < 10: trending.append(data_obj)
                    # Jika dari header "Korean Drama"
                    elif "korean drama" in section_title or "drakor" in section_title:
                        if len(kdrama) < 12: kdrama.append(data_obj)
                    # Jika dari header "Film Terbaru"
                    elif "film terbaru" in section_title or "movie" in section_title:
                        if len(movies) < 12: movies.append(data_obj)
                    else:
                        # Fallback jika tidak punya header spesifik
                        if media_type == 'series' and len(kdrama) < 12:
                            kdrama.append(data_obj)
                        elif media_type == 'movie' and len(movies) < 12:
                            movies.append(data_obj)

                except Exception as e:
                    continue
        
        print(f"[*] Berhasil menyaring data modern: Hero({len(hero)}), Trending({len(trending)}), KDrama({len(kdrama)}), Movies({len(movies)})")

        return jsonify({
            "hero": hero,
            "trending": trending,
            "kdrama": kdrama,
            "movies": movies
        })
        
    except Exception as e:
        print(f"[X] Kesalahan sistem: {str(e)}")
        return jsonify({
            "error": str(e),
            "hero": [], "trending": [], "kdrama": [], "movies": []
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
