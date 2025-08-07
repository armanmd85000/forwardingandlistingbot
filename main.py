# Ultimate Forward & Batch Bot - Enhanced Version
# Merged features from VJ-Forward-Bot and Gita1 with Inline Interface
# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ

import re
import asyncio
import time
import logging
from typing import Optional, Tuple, Dict, Union, List, AsyncGenerator
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode, MessageMediaType, ChatType, ChatMemberStatus
from pyrogram.errors import (
    FloodWait, RPCError, MessageIdInvalid, ChannelInvalid,
    ChatAdminRequired, PeerIdInvalid, UserNotParticipant, BadRequest
)
from logging.handlers import RotatingFileHandler

# Import configuration
from config import Config, temp

# Enhanced Configuration Class
class BotConfig:
    # Original VJ Bot settings
    BOT_TOKEN = Config.BOT_TOKEN
    API_ID = Config.API_ID
    API_HASH = Config.API_HASH
    BOT_OWNER = Config.BOT_OWNER
    
    # Advanced Batch Processing settings
    OFFSET = 0
    PROCESSING = False
    BATCH_MODE = False
    PHOTO_FORWARD_MODE = False
    AUTO_FORWARD_MODE = False
    SOURCE_CHAT = None
    TARGET_CHAT = None
    START_ID = None
    END_ID = None
    CURRENT_TASK = None
    REPLACEMENTS = {}
    ADMIN_CACHE = {}
    
    # Forward settings from VJ Bot
    FORWARD_RULES = {}
    
    MESSAGE_FILTERS = {
        'text': True,
        'photo': True,
        'video': True,
        'document': True,
        'audio': True,
        'animation': True,
        'voice': True,
        'video_note': True,
        'sticker': True,
        'poll': True,
        'contact': True
    }
    
    # Performance settings
    MAX_RETRIES = Config.MAX_RETRIES
    DELAY_BETWEEN_MESSAGES = Config.DELAY_BETWEEN_MESSAGES
    MAX_MESSAGES_PER_BATCH = Config.MAX_BATCH_SIZE
    SLEEP_THRESHOLD = Config.SLEEP_THRESHOLD
    
    # UI Settings
    CAPTION_MODE = True
    BUTTON_MODE = False
    SKIP_DUPLICATE = True

# Initialize the bot
app = Client(
    "UltimateForwardBatchBot",
    bot_token=BotConfig.BOT_TOKEN,
    api_id=BotConfig.API_ID,
    api_hash=BotConfig.API_HASH,
    sleep_threshold=BotConfig.SLEEP_THRESHOLD
)

# Logging setup
logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s (%(filename)s:%(lineno)d)",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("bot.log", maxBytes=50000000, backupCount=10),
        logging.StreamHandler()
    ],
    level=logging.INFO
)

# ====================== INLINE KEYBOARD FUNCTIONS ======================
def get_main_keyboard():
    """Main settings keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 Bot Settings", callback_data="bot_settings"),
            InlineKeyboardButton("📢 Channel Settings", callback_data="channel_settings")
        ],
        [
            InlineKeyboardButton("📝 Caption Settings", callback_data="caption_settings"),
            InlineKeyboardButton("🔘 Button Settings", callback_data="button_settings")
        ],
        [
            InlineKeyboardButton("🔍 Filters", callback_data="filters"),
            InlineKeyboardButton("⚙️ Extra Settings", callback_data="extra_settings")
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]
    ])

def get_bot_settings_keyboard():
    """Bot settings keyboard"""
    auto_status = "✅ ON" if BotConfig.AUTO_FORWARD_MODE else "❌ OFF"
    batch_status = "✅ Ready" if not BotConfig.PROCESSING else "⚠️ Processing"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔄 Auto Forward: {auto_status}", callback_data="toggle_auto")],
        [InlineKeyboardButton(f"⚡ Batch Mode: {batch_status}", callback_data="batch_mode")],
        [InlineKeyboardButton("📸 Photo Forward", callback_data="photo_forward")],
        [InlineKeyboardButton("🔗 Set Source Chat", callback_data="set_source")],
        [InlineKeyboardButton("🎯 Set Target Chat", callback_data="set_target")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ])

def get_caption_settings_keyboard():
    """Caption settings keyboard"""
    caption_status = "✅ ON" if BotConfig.CAPTION_MODE else "❌ OFF"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📝 Caption Mode: {caption_status}", callback_data="toggle_caption")],
        [InlineKeyboardButton(f"🔢 Current Offset: {BotConfig.OFFSET}", callback_data="set_offset")],
        [InlineKeyboardButton("➕ Add Number", callback_data="add_number")],
        [InlineKeyboardButton("➖ Less Number", callback_data="less_number")],
        [InlineKeyboardButton("📝 Word Replacements", callback_data="word_replacements")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ])

def get_filters_keyboard():
    """Filters settings keyboard"""
    keyboard = []
    
    # Create rows of filter buttons (2 per row)
    filter_items = list(BotConfig.MESSAGE_FILTERS.items())
    for i in range(0, len(filter_items), 2):
        row = []
        for j in range(2):
            if i + j < len(filter_items):
                filter_type, enabled = filter_items[i + j]
                status = "✅" if enabled else "❌"
                row.append(InlineKeyboardButton(
                    f"{status} {filter_type.title()}", 
                    callback_data=f"toggle_filter_{filter_type}"
                ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_extra_settings_keyboard():
    """Extra settings keyboard"""
    skip_status = "✅ ON" if BotConfig.SKIP_DUPLICATE else "❌ OFF"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏭️ Skip Duplicate: {skip_status}", callback_data="toggle_skip")],
        [InlineKeyboardButton(f"⏱️ Delay: {BotConfig.DELAY_BETWEEN_MESSAGES}s", callback_data="set_delay")],
        [InlineKeyboardButton(f"🔄 Max Retries: {BotConfig.MAX_RETRIES}", callback_data="set_retries")],
        [InlineKeyboardButton("🔄 Reset All Settings", callback_data="reset_all")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ])

# ====================== UTILITY FUNCTIONS ======================
def is_not_command(_, __, message: Message) -> bool:
    return not (message.text and message.text.startswith('/'))

def parse_message_link(text: str) -> Optional[Tuple[Union[int, str], int]]:
    """Parse Telegram message link and return (chat_id, message_id) tuple"""
    pattern = r'(?:https?://)?(?:t\.me|telegram\.(?:me|dog))/(?:c/)?([^/\s]+)/(\d+)'
    match = re.search(pattern, text)
    if match:
        chat_id = match.group(1)
        message_id = int(match.group(2))
        return (chat_id, message_id)
    return None

def generate_message_link(chat: object, message_id: int) -> str:
    """Generate message link for a chat and message ID"""
    if hasattr(chat, 'username') and chat.username:
        return f"https://t.me/{chat.username}/{message_id}"
    else:
        chat_id_str = str(chat.id).replace('-100', '')
        return f"https://t.me/c/{chat_id_str}/{message_id}"

def modify_content(text: str, offset: int) -> str:
    if not text:
        return text

    # Apply word replacements
    for original, replacement in sorted(BotConfig.REPLACEMENTS.items(), key=lambda x: (-len(x[0]), x[0].lower())):
        text = re.sub(rf'\b{re.escape(original)}\b', replacement, text, flags=re.IGNORECASE)

    # Modify Telegram links
    def replacer(match):
        prefix = match.group(1) or ""
        domain = match.group(2)
        chat_part = match.group(3) or ""
        chat_id = match.group(4)
        post_id = match.group(5)
        return f"{prefix}{domain}/{chat_part}{chat_id}/{int(post_id) + offset}"

    pattern = r'(https?://)?(t\.me|telegram\.(?:me|dog))/(c/)?([^/\s]+)/(\d+)'
    return re.sub(pattern, replacer, text)

async def verify_permissions(client: Client, chat_id: Union[int, str]) -> Tuple[bool, str]:
    try:
        if isinstance(chat_id, str):
            chat = await client.get_chat(chat_id)
            chat_id = chat.id

        if chat_id in BotConfig.ADMIN_CACHE:
            return BotConfig.ADMIN_CACHE[chat_id]

        chat = await client.get_chat(chat_id)
        
        if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
            result = (False, "Only channels and supergroups are supported")
            BotConfig.ADMIN_CACHE[chat_id] = result
            return result
            
        try:
            member = await client.get_chat_member(chat.id, "me")
        except UserNotParticipant:
            result = (False, "Bot is not a member of this chat")
            BotConfig.ADMIN_CACHE[chat_id] = result
            return result
            
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            result = (False, "Bot needs to be admin")
            BotConfig.ADMIN_CACHE[chat_id] = result
            return result
        
        result = (True, "OK")
        BotConfig.ADMIN_CACHE[chat_id] = result
        return result
        
    except (ChannelInvalid, PeerIdInvalid):
        return (False, "Invalid chat ID")
    except Exception as e:
        return (False, f"Error: {str(e)}")

async def process_message(client: Client, source_msg: Message, target_chat_id: int) -> bool:
    for attempt in range(BotConfig.MAX_RETRIES):
        try:
            if source_msg.service or source_msg.empty:
                return False
                
            media_type = source_msg.media
            if media_type and BotConfig.MESSAGE_FILTERS.get(media_type.value, False):
                caption = source_msg.caption or "" if BotConfig.CAPTION_MODE else ""
                modified_caption = modify_content(caption, BotConfig.OFFSET)
                
                media_mapping = {
                    MessageMediaType.PHOTO: client.send_photo,
                    MessageMediaType.VIDEO: client.send_video,
                    MessageMediaType.DOCUMENT: client.send_document,
                    MessageMediaType.AUDIO: client.send_audio,
                    MessageMediaType.ANIMATION: client.send_animation,
                    MessageMediaType.VOICE: client.send_voice,
                    MessageMediaType.VIDEO_NOTE: client.send_video_note,
                    MessageMediaType.STICKER: client.send_sticker
                }
                
                if media_type in media_mapping:
                    kwargs = {
                        'chat_id': target_chat_id,
                        'caption': modified_caption if media_type != MessageMediaType.STICKER else None,
                        'parse_mode': ParseMode.MARKDOWN
                    }
                    kwargs[media_type.value] = getattr(source_msg, media_type.value).file_id
                    
                    await media_mapping[media_type](**kwargs)
                    return True
                else:
                    await client.copy_message(
                        chat_id=target_chat_id,
                        from_chat_id=source_msg.chat.id,
                        message_id=source_msg.id,
                        caption=modified_caption,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return True
            elif source_msg.text and BotConfig.MESSAGE_FILTERS['text']:
                await client.send_message(
                    chat_id=target_chat_id,
                    text=modify_content(source_msg.text, BotConfig.OFFSET),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=source_msg.reply_markup if BotConfig.BUTTON_MODE else None
                )
                return True
                
            return False
            
        except FloodWait as e:
            if attempt == BotConfig.MAX_RETRIES - 1:
                raise
            await asyncio.sleep(e.value)
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed for message {source_msg.id}: {e}")
            if attempt == BotConfig.MAX_RETRIES - 1:
                return False
            await asyncio.sleep(1)
    
    return False

async def process_photo_with_link(client: Client, source_msg: Message, target_chat_id: int) -> bool:
    """Process photo message and send with link included in caption"""
    for attempt in range(BotConfig.MAX_RETRIES):
        try:
            if source_msg.service or source_msg.empty or not source_msg.photo:
                return False
            
            caption = source_msg.caption or "" if BotConfig.CAPTION_MODE else ""
            modified_caption = modify_content(caption, BotConfig.OFFSET)
            message_link = generate_message_link(source_msg.chat, source_msg.id)
            
            if modified_caption:
                final_caption = f"{modified_caption}\n\n🔗 **Link:** {message_link}"
            else:
                final_caption = f"🔗 **Link:** {message_link}"
            
            await client.send_photo(
                chat_id=target_chat_id,
                photo=source_msg.photo.file_id,
                caption=final_caption,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return True
            
        except FloodWait as e:
            if attempt == BotConfig.MAX_RETRIES - 1:
                raise
            await asyncio.sleep(e.value)
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed for photo message {source_msg.id}: {e}")
            if attempt == BotConfig.MAX_RETRIES - 1:
                return False
            await asyncio.sleep(1)
    
    return False

# ====================== COMMAND HANDLERS ======================
@app.on_message(filters.command(["start", "help"]))
async def start_cmd(client: Client, message: Message):
    help_text = """
🚀 **Ultimate Forward & Batch Bot** 📝

🔹 **Enhanced Features:**
✅ Advanced batch processing (up to 100K messages)
✅ Smart link modification with offset
✅ Word replacement system
✅ Photo forwarding with embedded links
✅ Auto-forwarding rules
✅ Interactive settings panel
✅ Multiple media type support
✅ Flood protection & retry mechanism

🔹 **Quick Commands:**
/settings - Open settings panel
/batch - Start batch processing
/photoforward - Photo forwarding mode
/status - Show current configuration

📊 **Batch Limit:** Up to 100,000 messages per batch
⚡ **Interface:** Modern button-based UI
🔗 **Credits:** @VJ_Botz | Subscribe: @Tech_VJ

Click /settings to access the interactive control panel! 👆
"""
    await message.reply(
        help_text, 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Open Settings", callback_data="main_menu")]
        ])
    )

@app.on_message(filters.command("settings"))
async def settings_cmd(client: Client, message: Message):
    status_text = f"""
⚙️ **Bot Settings Panel**

🔹 **Current Configuration:**
▫️ **Auto-Forward:** {'✅ Enabled' if BotConfig.AUTO_FORWARD_MODE else '❌ Disabled'}
▫️ **Caption Mode:** {'✅ Enabled' if BotConfig.CAPTION_MODE else '❌ Disabled'}
▫️ **Current Offset:** {BotConfig.OFFSET}
▫️ **Processing:** {'⚠️ Active' if BotConfig.PROCESSING else '✅ Ready'}

🔹 **Chat Configuration:**
▫️ **Source:** {BotConfig.SOURCE_CHAT.title if BotConfig.SOURCE_CHAT else 'Not Set'}
▫️ **Target:** {BotConfig.TARGET_CHAT.title if BotConfig.TARGET_CHAT else 'Not Set'}

Choose an option below to configure:
"""
    await message.reply(
        status_text, 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ====================== CALLBACK QUERY HANDLERS ======================
@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    try:
        if data == "main_menu":
            status_text = f"""
⚙️ **Bot Settings Panel**

🔹 **Current Configuration:**
▫️ **Auto-Forward:** {'✅ Enabled' if BotConfig.AUTO_FORWARD_MODE else '❌ Disabled'}
▫️ **Caption Mode:** {'✅ Enabled' if BotConfig.CAPTION_MODE else '❌ Disabled'}
▫️ **Current Offset:** {BotConfig.OFFSET}
▫️ **Processing:** {'⚠️ Active' if BotConfig.PROCESSING else '✅ Ready'}

🔹 **Chat Configuration:**
▫️ **Source:** {BotConfig.SOURCE_CHAT.title if BotConfig.SOURCE_CHAT else 'Not Set'}
▫️ **Target:** {BotConfig.TARGET_CHAT.title if BotConfig.TARGET_CHAT else 'Not Set'}

Choose an option below to configure:
"""
            await callback_query.edit_message_text(
                status_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard()
            )

        elif data == "bot_settings":
            await callback_query.edit_message_text(
                "🤖 **Bot Settings**\n\nConfigure bot behavior and forwarding rules:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_bot_settings_keyboard()
            )

        elif data == "caption_settings":
            await callback_query.edit_message_text(
                f"📝 **Caption Settings**\n\n**Current Offset:** {BotConfig.OFFSET}\n**Replacements:** {len(BotConfig.REPLACEMENTS)} active\n\nConfigure text and link modifications:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_caption_settings_keyboard()
            )

        elif data == "filters":
            enabled_count = sum(BotConfig.MESSAGE_FILTERS.values())
            total_count = len(BotConfig.MESSAGE_FILTERS)
            await callback_query.edit_message_text(
                f"🔍 **Message Filters**\n\n**Active Filters:** {enabled_count}/{total_count}\n\nToggle message types to filter:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_filters_keyboard()
            )

        elif data == "extra_settings":
            await callback_query.edit_message_text(
                f"⚙️ **Extra Settings**\n\n**Delay:** {BotConfig.DELAY_BETWEEN_MESSAGES}s between messages\n**Max Retries:** {BotConfig.MAX_RETRIES}\n**Skip Duplicate:** {'✅ ON' if BotConfig.SKIP_DUPLICATE else '❌ OFF'}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_extra_settings_keyboard()
            )

        elif data == "toggle_auto":
            BotConfig.AUTO_FORWARD_MODE = not BotConfig.AUTO_FORWARD_MODE
            status = "✅ Enabled" if BotConfig.AUTO_FORWARD_MODE else "❌ Disabled"
            await callback_query.answer(f"Auto-Forward {status}")
            await callback_query.edit_message_reply_markup(reply_markup=get_bot_settings_keyboard())

        elif data == "toggle_caption":
            BotConfig.CAPTION_MODE = not BotConfig.CAPTION_MODE
            status = "✅ Enabled" if BotConfig.CAPTION_MODE else "❌ Disabled"
            await callback_query.answer(f"Caption Mode {status}")
            await callback_query.edit_message_reply_markup(reply_markup=get_caption_settings_keyboard())

        elif data == "toggle_skip":
            BotConfig.SKIP_DUPLICATE = not BotConfig.SKIP_DUPLICATE
            status = "✅ Enabled" if BotConfig.SKIP_DUPLICATE else "❌ Disabled"
            await callback_query.answer(f"Skip Duplicate {status}")
            await callback_query.edit_message_reply_markup(reply_markup=get_extra_settings_keyboard())

        elif data.startswith("toggle_filter_"):
            filter_type = data.replace("toggle_filter_", "")
            BotConfig.MESSAGE_FILTERS[filter_type] = not BotConfig.MESSAGE_FILTERS[filter_type]
            status = "✅ Enabled" if BotConfig.MESSAGE_FILTERS[filter_type] else "❌ Disabled"
            await callback_query.answer(f"{filter_type.title()} filter {status}")
            await callback_query.edit_message_reply_markup(reply_markup=get_filters_keyboard())

        elif data == "batch_mode":
            if BotConfig.PROCESSING:
                await callback_query.answer("❌ Already processing! Use /stop to cancel", show_alert=True)
            else:
                await callback_query.answer("✅ Batch mode ready! Use /batch to start")

        elif data == "photo_forward":
            if BotConfig.PROCESSING:
                await callback_query.answer("❌ Already processing! Use /stop to cancel", show_alert=True)
            else:
                await callback_query.answer("✅ Photo forward ready! Use /photoforward to start")

        elif data == "status":
            status_text = f"""
📊 **Detailed Status**

🔹 **Bot State:**
▫️ Processing: {'⚠️ Active' if BotConfig.PROCESSING else '✅ Ready'}
▫️ Auto-Forward: {'✅ ON' if BotConfig.AUTO_FORWARD_MODE else '❌ OFF'}
▫️ Batch Mode: {'✅ ON' if BotConfig.BATCH_MODE else '❌ OFF'}
▫️ Photo Mode: {'✅ ON' if BotConfig.PHOTO_FORWARD_MODE else '❌ OFF'}

🔹 **Settings:**
▫️ Offset: {BotConfig.OFFSET}
▫️ Max Batch: {BotConfig.MAX_MESSAGES_PER_BATCH:,}
▫️ Delay: {BotConfig.DELAY_BETWEEN_MESSAGES}s
▫️ Retries: {BotConfig.MAX_RETRIES}

🔹 **Filters:** {sum(BotConfig.MESSAGE_FILTERS.values())}/{len(BotConfig.MESSAGE_FILTERS)} active
🔹 **Replacements:** {len(BotConfig.REPLACEMENTS)} rules
"""
            await callback_query.edit_message_text(
                status_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
                ])
            )

        elif data == "reset_all":
            BotConfig.OFFSET = 0
            BotConfig.REPLACEMENTS = {}
            BotConfig.PROCESSING = False
            BotConfig.BATCH_MODE = False
            BotConfig.PHOTO_FORWARD_MODE = False
            BotConfig.AUTO_FORWARD_MODE = False
            BotConfig.MESSAGE_FILTERS = {k: True for k in BotConfig.MESSAGE_FILTERS}
            await callback_query.answer("✅ All settings reset to defaults")
            await callback_query.edit_message_reply_markup(reply_markup=get_extra_settings_keyboard())

        elif data == "close":
            await callback_query.message.delete()

        else:
            await callback_query.answer("🚧 Feature coming soon!")

    except Exception as e:
        logging.error(f"Callback error: {e}")
        await callback_query.answer("❌ An error occurred")

# ====================== ORIGINAL COMMAND HANDLERS ======================
@app.on_message(filters.command("batch"))
async def start_batch(client: Client, message: Message):
    if BotConfig.PROCESSING:
        return await message.reply("⚠️ Already processing! Use /stop to cancel")
    
    if not BotConfig.SOURCE_CHAT:
        return await message.reply("❌ Source chat not set. Use settings panel to configure")
    
    BotConfig.PROCESSING = True
    BotConfig.BATCH_MODE = True
    BotConfig.PHOTO_FORWARD_MODE = False
    BotConfig.START_ID = None
    BotConfig.END_ID = None
    
    await message.reply(
        f"🔹 **Batch Mode Activated**\n"
        f"▫️ Source: {BotConfig.SOURCE_CHAT.title}\n"
        f"▫️ Target: {BotConfig.TARGET_CHAT.title if BotConfig.TARGET_CHAT else 'Current Chat'}\n"
        f"▫️ Offset: {BotConfig.OFFSET}\n"
        f"▫️ Replacements: {len(BotConfig.REPLACEMENTS)}\n"
        f"▫️ Max Batch: {BotConfig.MAX_MESSAGES_PER_BATCH:,} messages\n\n"
        f"Reply to the FIRST message or send its link",
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command("photoforward"))
async def start_photo_forward(client: Client, message: Message):
    if BotConfig.PROCESSING:
        return await message.reply("⚠️ Already processing! Use /stop to cancel")
    
    if not BotConfig.SOURCE_CHAT:
        return await message.reply("❌ Source chat not set. Use settings panel to configure")
    
    BotConfig.PROCESSING = True
    BotConfig.PHOTO_FORWARD_MODE = True
    BotConfig.BATCH_MODE = False
    BotConfig.START_ID = None
    BotConfig.END_ID = None
    
    await message.reply(
        f"📸 **Photo Forward Mode Activated**\n"
        f"▫️ Source: {BotConfig.SOURCE_CHAT.title}\n"
        f"▫️ Target: {BotConfig.TARGET_CHAT.title if BotConfig.TARGET_CHAT else 'Current Chat'}\n"
        f"▫️ Filter: Photos only with embedded links\n\n"
        f"Reply to the FIRST message or send its link",
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command(["stop", "cancel"]))
async def stop_cmd(client: Client, message: Message):
    if BotConfig.PROCESSING:
        BotConfig.PROCESSING = False
        BotConfig.BATCH_MODE = False
        BotConfig.PHOTO_FORWARD_MODE = False
        if BotConfig.CURRENT_TASK:
            BotConfig.CURRENT_TASK.cancel()
            BotConfig.CURRENT_TASK = None
        await message.reply("✅ Processing stopped")
    else:
        await message.reply("⚠️ No active process")

@app.on_message(filters.command(["addnumber", "addnum"]))
async def add_offset(client: Client, message: Message):
    try:
        offset = int(message.command[1])
        BotConfig.OFFSET += offset
        await message.reply(f"✅ Offset increased by {offset}. New offset: {BotConfig.OFFSET}")
    except (IndexError, ValueError):
        await message.reply("❌ Please provide a valid number to add")

@app.on_message(filters.command("setchat"))
async def set_chat(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            return await message.reply("Usage: /setchat [source|target] [chat_id or username]")
        
        chat_type = message.command[1].lower()
        if chat_type not in ["source", "target"]:
            return await message.reply("Invalid type. Use 'source' or 'target'")
        
        if message.reply_to_message:
            chat = message.reply_to_message.chat
        elif len(message.command) > 2:
            chat_id = message.command[2]
            try:
                chat = await client.get_chat(chat_id)
            except Exception as e:
                return await message.reply(f"Invalid chat: {str(e)}")
        else:
            chat = message.chat
        
        has_perms, perm_msg = await verify_permissions(client, chat.id)
        if not has_perms:
            return await message.reply(f"Permission error: {perm_msg}")
        
        if chat_type == "source":
            BotConfig.SOURCE_CHAT = chat
        else:
            BotConfig.TARGET_CHAT = chat
        
        await message.reply(
            f"✅ {'Source' if chat_type == 'source' else 'Target'} chat set to:\n"
            f"**Title:** {chat.title}\n"
            f"**ID:** {chat.id}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

# ====================== BATCH PROCESSING FUNCTIONS ======================
async def process_batch(client: Client, message: Message):
    try:
        if not BotConfig.SOURCE_CHAT:
            await message.reply("❌ Source chat not set")
            BotConfig.PROCESSING = False
            return
            
        start_id = min(BotConfig.START_ID, BotConfig.END_ID)
        end_id = max(BotConfig.START_ID, BotConfig.END_ID)
        total = end_id - start_id + 1
        
        if total > BotConfig.MAX_MESSAGES_PER_BATCH:
            await message.reply(f"❌ Batch too large ({total:,} messages). Max: {BotConfig.MAX_MESSAGES_PER_BATCH:,}")
            BotConfig.PROCESSING = False
            return
            
        target_chat = BotConfig.TARGET_CHAT.id if BotConfig.TARGET_CHAT else message.chat.id
        
        progress_msg = await message.reply(
            f"⚡ **Batch Processing Started**\n"
            f"▫️ **Range:** {start_id:,}-{end_id:,}\n"
            f"▫️ **Total:** {total:,} messages\n"
            f"▫️ **Offset:** {BotConfig.OFFSET}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        processed = failed = 0
        last_update = time.time()
        
        for current_id in range(start_id, end_id + 1):
            if not BotConfig.PROCESSING:
                break
            
            try:
                msg = await client.get_messages(BotConfig.SOURCE_CHAT.id, current_id)
                if msg and not msg.empty:
                    success = await process_message(client, msg, target_chat)
                    if success:
                        processed += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                
                if time.time() - last_update >= 5 or current_id == end_id:
                    progress = ((current_id - start_id) / total) * 100
                    try:
                        await progress_msg.edit(
                            f"⚡ **Processing Batch**\n"
                            f"▫️ **Progress:** {progress:.1f}%\n"
                            f"▫️ **Current:** {current_id:,}\n"
                            f"✅ **Success:** {processed:,}\n"
                            f"❌ **Failed:** {failed:,}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        last_update = time.time()
                    except:
                        pass
                
                await asyncio.sleep(BotConfig.DELAY_BETWEEN_MESSAGES)
            except FloodWait as e:
                await progress_msg.edit(f"⏳ Flood wait: {e.value}s...")
                await asyncio.sleep(e.value)
            except Exception as e:
                logging.error(f"Error processing {current_id}: {e}")
                failed += 1
                await asyncio.sleep(1)
        
        if BotConfig.PROCESSING:
            await progress_msg.edit(
                f"✅ **Batch Complete!**\n"
                f"▫️ **Total:** {total:,}\n"
                f"✅ **Success:** {processed:,}\n"
                f"❌ **Failed:** {failed:,}\n"
                f"▫️ **Success Rate:** {(processed/total)*100:.1f}%",
                parse_mode=ParseMode.MARKDOWN
            )
    
    except Exception as e:
        await message.reply(f"❌ Batch failed: {str(e)}")
    finally:
        BotConfig.PROCESSING = False
        BotConfig.BATCH_MODE = False
        BotConfig.CURRENT_TASK = None

async def process_photo_batch(client: Client, message: Message):
    try:
        if not BotConfig.SOURCE_CHAT:
            await message.reply("❌ Source chat not set")
            BotConfig.PROCESSING = False
            return
            
        start_id = min(BotConfig.START_ID, BotConfig.END_ID)
        end_id = max(BotConfig.START_ID, BotConfig.END_ID)
        total = end_id - start_id + 1
        
        if total > BotConfig.MAX_MESSAGES_PER_BATCH:
            await message.reply(f"❌ Batch too large ({total:,} messages). Max: {BotConfig.MAX_MESSAGES_PER_BATCH:,}")
            BotConfig.PROCESSING = False
            return
            
        target_chat = BotConfig.TARGET_CHAT.id if BotConfig.TARGET_CHAT else message.chat.id
        
        progress_msg = await message.reply(
            f"📸 **Photo Forward Processing Started**\n"
            f"▫️ **Range:** {start_id:,}-{end_id:,}\n"
            f"▫️ **Total Messages:** {total:,}\n"
            f"▫️ **Filter:** Photos only with links",
            parse_mode=ParseMode.MARKDOWN
        )
        
        processed = photos_found = failed = 0
        last_update = time.time()
        
        for current_id in range(start_id, end_id + 1):
            if not BotConfig.PROCESSING:
                break
            
            try:
                msg = await client.get_messages(BotConfig.SOURCE_CHAT.id, current_id)
                if msg and not msg.empty:
                    processed += 1
                    if msg.photo:
                        photos_found += 1
                        success = await process_photo_with_link(client, msg, target_chat)
                        if not success:
                            failed += 1
                
                if time.time() - last_update >= 5 or current_id == end_id:
                    progress = ((current_id - start_id) / total) * 100
                    try:
                        await progress_msg.edit(
                            f"📸 **Processing Photo Batch**\n"
                            f"▫️ **Progress:** {progress:.1f}%\n"
                            f"▫️ **Current:** {current_id:,}\n"
                            f"📝 **Checked:** {processed:,}\n"
                            f"📸 **Photos Found:** {photos_found:,}\n"
                            f"❌ **Failed:** {failed:,}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        last_update = time.time()
                    except:
                        pass
                
                await asyncio.sleep(BotConfig.DELAY_BETWEEN_MESSAGES)
            except FloodWait as e:
                await progress_msg.edit(f"⏳ Flood wait: {e.value}s...")
                await asyncio.sleep(e.value)
            except Exception as e:
                logging.error(f"Error processing {current_id}: {e}")
                failed += 1
                await asyncio.sleep(1)
        
        if BotConfig.PROCESSING:
            success_photos = photos_found - failed
            await progress_msg.edit(
                f"✅ **Photo Forward Complete!**\n"
                f"📝 **Total Checked:** {processed:,}\n"
                f"📸 **Photos Found:** {photos_found:,}\n"
                f"✅ **Successfully Forwarded:** {success_photos:,}\n"
                f"❌ **Failed:** {failed:,}\n"
                f"📊 **Success Rate:** {(success_photos/photos_found)*100:.1f}%" if photos_found > 0 else "📊 No photos found",
                parse_mode=ParseMode.MARKDOWN
            )
    
    except Exception as e:
        await message.reply(f"❌ Photo batch failed: {str(e)}")
    finally:
        BotConfig.PROCESSING = False
        BotConfig.PHOTO_FORWARD_MODE = False
        BotConfig.CURRENT_TASK = None

# Message handler for batch processing and auto-forward
@app.on_message(filters.text & filters.create(is_not_command))
async def handle_message(client: Client, message: Message):
    # Auto-forward handler
    if (BotConfig.AUTO_FORWARD_MODE and 
        BotConfig.SOURCE_CHAT and 
        BotConfig.TARGET_CHAT and 
        message.chat.id == BotConfig.SOURCE_CHAT.id and
        not BotConfig.PROCESSING):
        
        try:
            await process_message(client, message, BotConfig.TARGET_CHAT.id)
            temp.TOTAL_FORWARDED += 1
        except Exception as e:
            logging.error(f"Auto-forward failed: {e}")
            temp.TOTAL_FAILED += 1
        return
    
    # Batch processing handler
    if not BotConfig.PROCESSING:
        return
    
    try:
        # Get source message details
        if message.reply_to_message:
            source_msg = message.reply_to_message
            chat_id = source_msg.chat.id
            msg_id = source_msg.id
        else:
            link_info = parse_message_link(message.text)
            if not link_info:
                return await message.reply("❌ Invalid message link")
            
            chat_identifier, msg_id = link_info
            
            try:
                chat = await client.get_chat(chat_identifier)
                chat_id = chat.id
            except Exception as e:
                return await message.reply(f"❌ Could not resolve chat: {str(e)}")

        if BotConfig.BATCH_MODE or BotConfig.PHOTO_FORWARD_MODE:
            if BotConfig.START_ID is None:
                # First message of batch
                has_perms, perm_msg = await verify_permissions(client, chat_id)
                if not has_perms:
                    BotConfig.PROCESSING = False
                    return await message.reply(f"❌ Permission error: {perm_msg}")
                
                if BotConfig.SOURCE_CHAT and chat_id != BotConfig.SOURCE_CHAT.id:
                    return await message.reply("❌ First message must be from the source chat")
                
                BotConfig.START_ID = msg_id
                mode_text = "Photo Forward" if BotConfig.PHOTO_FORWARD_MODE else "Batch"
                await message.reply(
                    f"✅ **First message set:** {msg_id}\n"
                    f"Now reply to the LAST message or send its link\n"
                    f"**Mode:** {mode_text}",
                    parse_mode=ParseMode.MARKDOWN
                )
            elif BotConfig.END_ID is None:
                # Second message of batch
                if not BotConfig.SOURCE_CHAT:
                    BotConfig.PROCESSING = False
                    return await message.reply("❌ Source chat not set")
                
                if chat_id != BotConfig.SOURCE_CHAT.id:
                    return await message.reply("❌ Last message must be from the same chat as source chat")
                
                BotConfig.END_ID = msg_id
                if BotConfig.PHOTO_FORWARD_MODE:
                    BotConfig.CURRENT_TASK = asyncio.create_task(process_photo_batch(client, message))
                else:
                    BotConfig.CURRENT_TASK = asyncio.create_task(process_batch(client, message))
        else:
            # Single message processing
            try:
                msg = await client.get_messages(chat_id, msg_id)
                if msg and not msg.empty:
                    target_chat = BotConfig.TARGET_CHAT.id if BotConfig.TARGET_CHAT else message.chat.id
                    success = await process_message(client, msg, target_chat)
                    if not success:
                        await message.reply("⚠️ Failed to process this message")
            except Exception as e:
                await message.reply(f"❌ Error: {str(e)}")
            
    except Exception as e:
        await message.reply(f"❌ Critical error: {str(e)}")
        BotConfig.PROCESSING = False
        BotConfig.BATCH_MODE = False
        BotConfig.PHOTO_FORWARD_MODE = False

# Main function
async def main():
    await app.start()
    bot_info = await app.get_me()
    print(f"✅ Bot Started: @{bot_info.username}")
    print(f"📊 Max Batch Size: {BotConfig.MAX_MESSAGES_PER_BATCH:,}")
    print("🚀 Ultimate Forward & Batch Bot with Enhanced UI is running!")
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
