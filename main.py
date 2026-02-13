import os
import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import Application

# ... (keep all your other imports and handlers here) ...

# 1. NEW: Professional Health Check Handler
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"ALIVE") # Choreo needs this to know the app is healthy

    def log_message(self, format, *args):
        return # Silence logs to keep Choreo console clean

def run_health_check_server():
    # Choreo provides the PORT variable automatically
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"✅ Health Check Server started on port {port}")
    server.serve_forever()

def main():
    # 2. Start Health Check in Background
    threading.Thread(target=run_health_check_server, daemon=True).start()

    # 3. Build Bot
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN is missing! Check Configs & Secrets in Choreo.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # (Add your handlers here exactly as before)
    app.add_handler(CommandHandler("start", start))
    # ... add all your other handlers/conv_handler here ...

    print("🚀 Assassin Codar Bot is starting polling...")
    
    # Use drop_pending_updates to avoid crashing on start
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
