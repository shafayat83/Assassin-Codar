from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import MONTHLY_PAY_URL, LIFETIME_PAY_URL

def get_payment_keyboard():
    keyboard = [
        [InlineKeyboardButton("💎 Monthly Plan - $5", url=MONTHLY_PAY_URL)],
        [InlineKeyboardButton("👑 Lifetime - $19 (Was ~~$50~~)", url=LIFETIME_PAY_URL)],
        [InlineKeyboardButton("✅ Verify Transaction", callback_data="start_verification")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)