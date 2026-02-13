import os
from dotenv import load_dotenv

load_dotenv()

# Tokens from Choreo Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Settings
CHANNEL_USERNAME = "@AssassinCodar"
GITHUB_API_URL = "https://models.inference.ai.azure.com/chat/completions"

# Payment Links
MONTHLY_PAY_URL = "https://commerce.coinbase.com/checkout/02550dac-5246-4355-9da9-6c849e071797"
LIFETIME_PAY_URL = "https://commerce.coinbase.com/checkout/ea3dd394-ab47-4330-96bf-d8159835d13e"
