import logging
import html
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_ID
from database import db
from ai_engine import generate_code
from payment import get_payment_keyboard

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

AWAITING_PROMPT, AWAITING_TXID = 1, 2

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
    keyboard.append([InlineKeyboardButton("👥 Invite", callback_data="menu_Invite")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args and context.args[0].isdigit():
        invite_id = int(context.args[0])
        if db.process_invite(user_id, invite_id):
            try:
                await context.bot.send_message(invite_id, f"🎁 *New Referr!* You earned 2 days PRO.")
            except: pass

    if not await is_user_member(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
                    [InlineKeyboardButton("🔄 Check Again", callback_data="check_membership")]]
        await update.message.reply_text("⚠️ Join our channel to unlock the bot:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text("⚡️ *Assassin Codar Bot Activated*", parse_mode="Markdown", reply_markup=await get_main_menu(user_id))

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    if query.data == "check_membership":
        if await is_user_member(user_id, context):
            await query.edit_message_text("✅ Verified! Use /start.")
        else: await query.answer("❌ Join @AssassinCodar first!", show_alert=True)
    elif query.data == "menu_plan":
        u = db.get_user(user_id)
        status = "💎 PRO" if db.is_user_pro(user_id) else "🆓 FREE"
        msg = f"👤 Plan: {status}\n📅 Expiry: `{u[1]}`\n📈 Usage: {u[2]}/5\n👥 Invite: {u[5]}"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]]))
    elif query.data == "menu_Invite":
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}?start={user_id}"
        await query.edit_message_text(f"👥 *Invite*\n\nEarn 2 days PRO per friend!\n\n🔗 `{link}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]]))
    elif query.data == "menu_upgrade":
        await query.edit_message_text("🚀 Choose your subscription plan:", reply_markup=get_payment_keyboard())
    elif query.data == "back_to_menu":
        await query.edit_message_text("⚡️ *Assassin Codar Menu*", reply_markup=await get_main_menu(user_id))

async def start_gen_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not db.is_user_pro(update.effective_user.id) and db.get_user(update.effective_user.id)[2] >= 5:
        await query.message.reply_text("❌ Limit reached! Invite someone or upgrade.")
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
    else: await update.message.reply_text("❌ AI Busy.")
    return ConversationHandler.END

async def start_pay_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("💳 Send TXID & Plan Name:")
    return AWAITING_TXID

async def process_txid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(ADMIN_ID, f"💰 *Payment Proof*\nID: `{update.effective_user.id}`\nMsg: {update.message.text}\n\n`/verify_month {update.effective_user.id}`\n`/verify_life {update.effective_user.id}`")
    await update.message.reply_text("✅ Proof sent to admin.")
    return ConversationHandler.END

async def admin_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        uid = int(context.args[0])
        if "month" in update.message.text: db.add_pro_days(uid, 30)
        else: db.set_lifetime_pro(uid)
        await update.message.reply_text(f"✅ User {uid} Upgraded.")
        await context.bot.send_message(uid, "🎉 Your account is now *PRO*!", parse_mode="Markdown")
    except: await update.message.reply_text("Usage: /verify_month ID")

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        uid = int(context.args[0])
        db.cancel_pro(uid)
        await update.message.reply_text(f"❌ User {uid} subscription cancelled.")
        await context.bot.send_message(uid, "⚠️ Your PRO subscription has been cancelled.")
    except: await update.message.reply_text("Usage: /cancel ID")

import asyncio

# ... (rest of your imports and handlers) ...

def main():
    """Main entry point using the modern Application builder."""
    # Build the application
    app = Application.builder().token(BOT_TOKEN).build()

    # Define the Conversation Handler
    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_gen_flow, pattern="^menu_generate$"),
            CallbackQueryHandler(start_pay_verify, pattern="^start_verification$")
        ],
        states={
            AWAITING_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_prompt)],
            AWAITING_TXID: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_txid)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify_month", admin_verify))
    app.add_handler(CommandHandler("verify_life", admin_verify))
    app.add_handler(CommandHandler("cancel", admin_cancel))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(handle_callbacks))

    print("✅ Assassin Codar Bot is Running...")

    # For Python 3.12+, run_polling is safer when handled like this
    # It handles its own event loop internally
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("\nBot stopped manually.")
    except Exception as e:
        print(f"🛑 Unexpected Error: {e}")
if __name__ == "__main__":
    main()