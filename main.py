import logging
import html
import os
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_ID
from database import db
from ai_engine import generate_code
from payment import get_payment_keyboard

# Logging
logging.basicConfig(level=logging.INFO)

# States
AWAITING_PROMPT, AWAITING_TXID = 1, 2

# --- DUMMY HTTP SERVER FOR CHOREO HEALTH CHECK ---
def run_health_check_server():
    port = int(os.getenv("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Health check server running on port {port}")
        httpd.serve_forever()

# --- BOT HANDLERS ---

async def is_user_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def get_main_menu(user_id):
    is_pro = db.is_user_pro(user_id)
    keyboard = [[InlineKeyboardButton("🔹 Generate Code", callback_data="menu_generate")]]
    row2 = [InlineKeyboardButton("📊 My Plan", callback_data="menu_plan")]
    if not is_pro:
        row2.append(InlineKeyboardButton("🚀 Upgrade to Pro", callback_data="menu_upgrade"))
    keyboard.append(row2)
    keyboard.append([InlineKeyboardButton("👥 Referral System", callback_data="menu_referral")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if context.args and context.args[0].isdigit():
        referrer_id = int(context.args[0])
        if db.process_referral(user_id, referrer_id):
            try:
                await context.bot.send_message(referrer_id, f"🎁 *New Referral!*\n\n{user.first_name} joined. You got *2 Days PRO*!", parse_mode="Markdown")
            except: pass

    if not await is_user_member(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
                    [InlineKeyboardButton("🔄 Check Again", callback_data="check_membership")]]
        await update.message.reply_text("⚠️ Join our channel to use the bot:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text("⚡️ *Assassin Codar Bot Activated*", parse_mode="Markdown", reply_markup=await get_main_menu(user_id))

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    if query.data == "check_membership":
        if await is_user_member(user_id, context):
            await query.edit_message_text("✅ Verified! Use /start to open menu.")
        else: await query.answer("❌ Join @AssassinCodar first!", show_alert=True)
    elif query.data == "menu_plan":
        u = db.get_user(user_id)
        status = "💎 PRO" if db.is_user_pro(user_id) else "🆓 FREE"
        msg = f"👤 *Your Profile*\n\n📜 Status: {status}\n📅 Expiry: `{u[1] if u[1] else 'None'}`\n📈 Usage: {u[2]}/5\n👥 Referrals: {u[5]}"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]]))
    elif query.data == "menu_referral":
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}?start={user_id}"
        await query.edit_message_text(f"👥 *Referral System*\n\nEarn 2 days PRO per friend!\n\n🔗 `{link}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]]))
    elif query.data == "menu_upgrade":
        await query.edit_message_text("🚀 *Upgrade Plans:*", reply_markup=get_payment_keyboard())
    elif query.data == "back_to_menu":
        await query.edit_message_text("⚡️ *Assassin Codar Menu*", reply_markup=await get_main_menu(user_id))

async def start_gen_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not db.is_user_pro(update.effective_user.id) and db.get_user(update.effective_user.id)[2] >= 5:
        await query.message.reply_text("❌ Daily limit reached!")
        return ConversationHandler.END
    await query.message.reply_text("💡 *What do you want to build?*", parse_mode="Markdown")
    return AWAITING_PROMPT

async def process_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⚔️ Coding...")
    code = generate_code(update.message.text)
    await status_msg.delete()
    if code:
        db.increment_usage(update.effective_user.id)
        await update.message.reply_html(f"<pre>{html.escape(code)}</pre>")
    else: await update.message.reply_text("❌ AI Error.")
    return ConversationHandler.END

async def start_pay_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("💳 Send Proof & Plan (Monthly/Life):")
    return AWAITING_TXID

async def process_txid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(ADMIN_ID, f"💰 *Payment Request*\nFrom: `{update.effective_user.id}`\nMsg: {update.message.text}\n\n`/verify_month {update.effective_user.id}`\n`/verify_life {update.effective_user.id}`")
    await update.message.reply_text("✅ Sent to admin for verification.")
    return ConversationHandler.END

async def admin_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        uid = int(context.args[0])
        if "month" in update.message.text.lower() or "verify_month" in update.message.text.lower():
            db.add_pro_days(uid, 30)
        else:
            db.set_lifetime_pro(uid)
        await update.message.reply_text(f"✅ User {uid} Activated.")
        await context.bot.send_message(uid, "🎉 *PRO Activated!*", parse_mode="Markdown")
    except: await update.message.reply_text("Usage: /verify_month ID")

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        tid = int(context.args[0])
        db.cancel_pro(tid)
        await update.message.reply_text(f"❌ Cancelled user {tid}")
        await context.bot.send_message(tid, "⚠️ Subscription cancelled.")
    except: await update.message.reply_text("Usage: /cancel ID")

def main():
    # Start the dummy health check server in a background thread
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_gen_flow, pattern="^menu_generate$"),
                      CallbackQueryHandler(start_pay_verify, pattern="^start_verification$")],
        states={AWAITING_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_prompt)],
                AWAITING_TXID: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_txid)]},
        fallbacks=[CommandHandler("start", start)])
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify_month", admin_verify))
    app.add_handler(CommandHandler("verify_life", admin_verify))
    app.add_handler(CommandHandler("cancel", admin_cancel))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    
    print("✅ Bot is polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
