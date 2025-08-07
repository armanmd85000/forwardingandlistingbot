# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

from os import environ 

class Config:
    # Core Bot Configuration
    API_ID = int(environ.get("API_ID", "25570420"))
    API_HASH = environ.get("API_HASH", "6591643fa39b5b9d0eb78cb24db17f69")
    BOT_TOKEN = environ.get("BOT_TOKEN", "")) 
    BOT_SESSION = environ.get("BOT_SESSION", "UltimateForwardBatchBot") 
    
    # Database Configuration (Optional - for future features)
    DATABASE_URI = environ.get("DATABASE_URI", "")
    DATABASE_NAME = environ.get("DATABASE_NAME", "ultimate-forward-batch-bot")
    
    # Bot Owner Configuration
    BOT_OWNER = int(environ.get("BOT_OWNER", "7552584508"))
    
    # Advanced Configuration for Batch Processing
    MAX_BATCH_SIZE = int(environ.get("MAX_BATCH_SIZE", "100000"))
    DELAY_BETWEEN_MESSAGES = float(environ.get("DELAY_BETWEEN_MESSAGES", "0.3"))
    MAX_RETRIES = int(environ.get("MAX_RETRIES", "3"))
    SLEEP_THRESHOLD = int(environ.get("SLEEP_THRESHOLD", "120"))
    
    # Enable/Disable Features
    ENABLE_AUTO_FORWARD = bool(environ.get("ENABLE_AUTO_FORWARD", "True"))
    ENABLE_BATCH_PROCESSING = bool(environ.get("ENABLE_BATCH_PROCESSING", "True"))
    ENABLE_PHOTO_FORWARD = bool(environ.get("ENABLE_PHOTO_FORWARD", "True"))
    
    # Logging Configuration
    LOG_LEVEL = environ.get("LOG_LEVEL", "INFO")
    LOG_FILE_NAME = environ.get("LOG_FILE_NAME", "bot.log")

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

class temp(object): 
    # Original VJ Bot temp variables
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
    
    # Enhanced temp variables for merged features
    PROCESSING_TASKS = {}
    BATCH_PROGRESS = {}
    FORWARD_RULES = {}
    ADMIN_CACHE = {}
    REPLACEMENTS_CACHE = {}
    
    # Statistics
    TOTAL_FORWARDED = 0
    TOTAL_PROCESSED = 0
    TOTAL_FAILED = 0

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
