# WAF Gateway & Secure Flask API Integration

Bu proje, Nginx tabanlı bir Web Application Firewall (WAF) ağ geçidinin (gateway) ve arka planda çalışan güvenli bir Flask RESTful API'ın (PostgreSQL ile birlikte) mikroservis mimarisinde entegrasyonunu içerir.

ModSecurity ve OWASP Core Rule Set (CRS) kullanılarak, OWASP Top 10 zafiyetlerine karşı (SQLi, XSS, Path Traversal vb.) aktif koruma sağlanmaktadır.

## 🏗️ Mimari Tasarım

Sistem üç ana bileşenden (Docker container) oluşmaktadır:

1.  **WAF Gateway (`flask-waf-gateway`):** Dışarıya açık tek noktadır (Port 8443). Nginx ve ModSecurity içerir. Gelen istekleri analiz eder, zararlı istekleri (XSS, SQLi) 403 Forbidden ile engeller, güvenli istekleri backend'e (Flask) iletir.
2.  **Application (`flask-waf-app`):** Sadece iç ağa açıktır. WAF'tan geçen temiz istekleri işleyen Flask RESTful API sunucusudur.
3.  **Database (`flask-waf-db`):** Sadece iç ağa açıktır. Kullanıcı ve oturum verilerini tutan PostgreSQL veritabanıdır.

```text
İstemci (curl/Tarayıcı)
       │
       ▼  HTTPS (8443)
┌─────────────────────────────────┐
│ Nginx + ModSecurity (Gateway)   │ ── Bloklar 🚫 (Zararlı İstek)
└──────────────┬──────────────────┘
               │  HTTP (5000) - Sadece İç Ağ
               ▼
┌─────────────────────────────────┐
│ Flask API (App)                 │
└──────────────┬──────────────────┘
               │  TCP (5432) - Sadece İç Ağ
               ▼
┌─────────────────────────────────┐
│ PostgreSQL 16 (DB)              │
└─────────────────────────────────┘
```

## 🔗 Git Submodule Yapısı

Bu proje, kod yönetimini modüler tutmak amacıyla "Git Submodule" yapısını kullanmaktadır. Arka planda çalışan Flask API kodu, ayrı bir bağımsız depo (repository) olarak geliştirilmiş olup, bu WAF projesine `app/` dizini altına bir alt modül olarak bağlanmıştır.

## 🚀 Kurulum ve Çalıştırma

### 1. Repoyu Klonlama (Submodule ile Birlikte)
Submodule (Flask API) dosyalarını da çekebilmek için `--recurse-submodules` parametresi zorunludur:
```bash
git clone --recurse-submodules https://github.com/onurolmus/flask-waf-project.git
cd flask-waf-project
```

### 2. Ortam Değişkenleri
Kök dizinde bir `.env` dosyası oluşturun:
```bash
cp .env.example .env
# Veya manuel olarak aşağıdaki içeriği oluşturun:
# SECRET_KEY=your-secret-key
# DB_USER=flaskuser
# DB_PASSWORD=flaskpass
# DB_HOST=db
# DB_PORT=5432
# DB_NAME=flaskdb
```

### 3. Sistemi Başlatma
Docker Compose kullanarak tüm servisleri ayağa kaldırın. WAF (ModSecurity) kaynak koddan derlendiği için ilk kurulum zaman alacaktır:
```bash
docker compose up -d --build
```

### 4. Veritabanı Tablolarını Oluşturma
Flask container'ının içinden migration işlemini çalıştırarak veritabanı tablolarını (`users`, `online_users`) oluşturun:
```bash
docker compose exec app flask db upgrade
```

## 🛡️ Güvenlik Testleri (OWASP Top 10)

Sistemin güvenlik duvarı (WAF) yeteneklerini doğrulamak için OWASP Top 10 standartlarında otomatik bir test paketi hazırlanmıştır. 

Testleri çalıştırmak için:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests
python tests/test_waf.py
```

### Desteklenen Test Senaryoları:
*   **A01 - Broken Access Control:** Path Traversal (`../../etc/passwd`)
*   **A03 - Injection:**
    *   SQL Injection (OR 1=1, UNION, DROP TABLE, Time-based)
    *   Cross-Site Scripting (Reflected, Stored, SVG onload, Event Handler)
    *   OS Command Injection (`cat /etc/passwd`)
*   **A05 - Security Misconfiguration:** Hassas dosya erişimi (`.env`, `config.py`)
*   **A07 - Authentication Failures:** User Enumeration, Zayıf parola engelleme
*   **A09 - Security Logging Failures:** ModSecurity atak loglama kontrolleri

ModSecurity kuralları "DetectionOnly" modundan "On" (Aktif Bloklama) moduna alınmıştır. Zararlı istekler doğrudan Nginx seviyesinde `403 Forbidden` ile engellenir ve Flask backend'ine asla ulaşamaz.
