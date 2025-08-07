# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

class Config:
    # Core Bot Configuration - PASTE YOUR VALUES HERE
    API_ID = 25570420  # Replace with your API_ID
    API_HASH = "6591643fa39b5b9d0eb78cb24db17f69"  # Replace with your API_HASH
    BOT_TOKEN = "7942215521:AAG5Zardlr7ULt2-yleqXeKjHKp4AQtVzd8"  # Replace with your BOT_TOKEN
    BOT_SESSION = "UltimateForwardBatchBot" 
    
    # Database Configuration (Optional)
    DATABASE_URI = ""  # MongoDB URI if you want database features
    DATABASE_NAME = "ultimate-forward-batch-bot"
    
    # Bot Owner Configuration
    BOT_OWNER = 7552584508  # Replace with your user ID
    
    # Advanced Configuration for Batch Processing
    MAX_BATCH_SIZE = 100000
    DELAY_BETWEEN_MESSAGES = 0.3
    MAX_RETRIES = 3
    SLEEP_THRESHOLD = 120
    
    # Enable/Disable Features
    ENABLE_AUTO_FORWARD = True
    ENABLE_BATCH_PROCESSING = True
    ENABLE_PHOTO_FORWARD = True
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FILE_NAME = "bot.log"

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
