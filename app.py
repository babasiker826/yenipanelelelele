from flask import Flask, render_template, request, jsonify, send_from_directory
import time
import os
from functools import wraps

app = Flask(__name__)

# SQL Injection ve Rate Limit koruması
def rate_limit(max_per_minute=60):
    def decorator(f):
        calls = []
        @wraps(f)
        def wrapped(*args, **kwargs):
            now = time.time()
            calls_in_time = [call for call in calls if call > now - 60]
            if len(calls_in_time) >= max_per_minute:
                return jsonify({"error": "Rate limit exceeded"}), 429
            calls.append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def sql_injection_protection(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # SQL injection karakterlerini kontrol et
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'union', 'select', 'drop', 'insert', 'update', 'delete']
        for arg in request.args.values():
            if any(char in arg.lower() for char in dangerous_chars):
                return jsonify({"error": "Invalid input"}), 400
        return f(*args, **kwargs)
    return wrapped

@app.route('/')
def index():
    return render_template('index.html')

# Static dosyalar için route
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Nabi API Proxy
@app.route('/api/nabi/<path:api_name>')
@rate_limit(max_per_minute=30)
@sql_injection_protection
def nabi_api(api_name):
    try:
        import requests
        
        # Nabi API base URL
        base_url = "https://nabi-sorgu-api.system.22web.org"
        
        # Tüm parametreleri al
        params = request.args.to_dict()
        
        # API endpoint'ini oluştur
        api_url = f"{base_url}/{api_name}"
        
        # API'ye istek yap
        response = requests.get(api_url, params=params, timeout=10)
        
        # Başarılı yanıtı döndür
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "success": False,
                "error": f"API error: {response.status_code}",
                "timestamp": time.time()
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "API timeout",
            "timestamp": time.time()
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"API connection error: {str(e)}",
            "timestamp": time.time()
        }), 502
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": time.time()
        }), 500

# NewVIP API Proxy
@app.route('/api/newvip/<path:api_name>')
@rate_limit(max_per_minute=30)
@sql_injection_protection
def newvip_api(api_name):
    try:
        import requests
        
        # NewVIP API base URL
        base_url = "https://newvip.nabi.22web.org/api"
        
        # Tüm parametreleri al
        params = request.args.to_dict()
        
        # API endpoint'ini oluştur
        api_url = f"{base_url}/{api_name}"
        
        # API'ye istek yap
        response = requests.get(api_url, params=params, timeout=10)
        
        # Başarılı yanıtı döndür
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "success": False,
                "error": f"API error: {response.status_code}",
                "timestamp": time.time()
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "API timeout",
            "timestamp": time.time()
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"API connection error: {str(e)}",
            "timestamp": time.time()
        }), 502
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": time.time()
        }), 500

# Health check endpoint - Render için gerekli
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time()})

# 404 hata sayfası
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

# 500 hata sayfası
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
