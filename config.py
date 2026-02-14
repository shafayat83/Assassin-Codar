import os
from dotenv import load_dotenv

load_dotenv()

# Get variables with safety defaults
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Safety for ADMIN_ID: If missing, default to 0 to prevent crash
admin_id_raw = os.getenv("ADMIN_ID")
ADMIN_ID = int(admin_id_raw) if admin_id_raw and admin_id_raw.isdigit() else 0

CHANNEL_USERNAME = "@AssassinCodar"
GITHUB_API_URL = "https://models.inference.ai.azure.com/chat/completions"
MONTHLY_PAY_URL = "https://commerce.coinbase.com/checkout/02550dac-5246-4355-9da9-6c849e071797"
LIFETIME_PAY_URL = "https://commerce.coinbase.com/checkout/ea3dd394-ab47-4330-96bf-d8159835d13e"
