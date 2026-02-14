import os
import threading
import logging
import html
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# 1. Setup Logging to see errors in Choreo "View Runtime" Logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Import your other files
try:
    from config import BOT_TOKEN, ADMIN_ID
    from database import db
    from ai_engine import generate_code
    from payment import get_payment_keyboard
except ImportError as e:
    logger.error(f"❌ Critical Import Error: {e}")
    sys.exit(1)

# States
AWAITING_PROMPT, AWAITING_TXID = 1, 2

# --- HEALTH CHECK SERVER (Tells Choreo the bot is working) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Assassin Codar is Running")

    def log_message(self, format, *args):
        return # Prevents flooding logs

def run_health_server():
    port = int(os.getenv("PORT", 8080))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"✅ Health Server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Health Server failed: {e}")

# --- BOT LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Logic for referral and menu...
    keyboard = [[InlineKeyboardButton("🔹 Generate Code", callback_data="menu_generate")]]
    await update.message.reply_text("⚡️ *Assassin Codar Ready*", parse_mode="Markdown", 
                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("💡 Describe what you want to build:")
    return AWAITING_PROMPT

async def process_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = await update.message.reply_text("⚔️ Coding...")
    code = generate_code(update.message.text)
    await status.delete()
    if code:
        await update.message.reply_html(f"<pre>{html.escape(code)}</pre>")
    return ConversationHandler.END

# --- MAIN EXECUTION ---

def main():
    # A. Start Health Check immediately in a separate thread
    threading.Thread(target=run_health_server, daemon=True).start()

    # B. Verify Token
    if not BOT_TOKEN or "YOUR_" in BOT_TOKEN:
        logger.error("❌ CRITICAL: BOT_TOKEN is missing or not set in Environment Variables!")
        return

    try:
        # C. Build Bot
        app = Application.builder().token(BOT_TOKEN).build()

        conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(handle_gen, pattern="^menu_generate$")],
            states={AWAITING_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_prompt)]},
            fallbacks=[CommandHandler("start", start)]
        )

        app.add_handler(CommandHandler("start", start))
        app.add_handler(conv)

        logger.info("🚀 Bot is starting polling...")
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Bot crashed during runtime: {e}")

if __name__ == "__main__":
    main()
