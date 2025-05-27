import re
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.enums import ParseMode, MessageMediaType
from pyrogram.errors import FloodWait

# Bot Configuration
API_ID = 20219694
API_HASH = "29d9b3a01721ab452fcae79346769e29"
BOT_TOKEN = "7972190756:AAHa4pUAZBTWSZ3smee9sEWiFv-lFhT5USA"

class Config:
    OFFSET = 0  # How much to add/subtract from message IDs in captions
    PROCESSING = False
    BATCH_MODE = False
    CHAT_ID = None
    START_ID = None
    END_ID = None

app = Client(
    "batch_link_modifier",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def is_not_command(_, __, message: Message):
    """Custom filter to identify non-command messages"""
    return not message.text.startswith('/')

def modify_telegram_links(text: str, offset: int) -> str:
    """Modifies only Telegram message links in text"""
    if not text:
        return text

    def replacer(match):
        full_url = match.group(0)
        msg_id = int(match.group(2))
        return full_url.replace(f"/{msg_id}", f"/{msg_id + offset}")

    # Pattern to match Telegram links (both t.me and telegram.me)
    pattern = r'https?://(?:t\.me|telegram\.me)/(?:c/)?\d+/\d+'
    return re.sub(pattern, replacer, text)

async def process_message(client: Client, source_msg: Message, target_chat_id: int):
    try:
        if source_msg.media:
            caption = source_msg.caption or ""
            modified_caption = modify_telegram_links(caption, Config.OFFSET)
            
            if source_msg.media == MessageMediaType.PHOTO:
                await client.send_photo(
                    chat_id=target_chat_id,
                    photo=source_msg.photo.file_id,
                    caption=modified_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif source_msg.media == MessageMediaType.VIDEO:
                await client.send_video(
                    chat_id=target_chat_id,
                    video=source_msg.video.file_id,
                    caption=modified_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif source_msg.media == MessageMediaType.DOCUMENT:
                await client.send_document(
                    chat_id=target_chat_id,
                    document=source_msg.document.file_id,
                    caption=modified_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # For other media types, try to send as document
                await client.send_document(
                    chat_id=target_chat_id,
                    document=source_msg.document.file_id,
                    caption=modified_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            modified_text = modify_telegram_links(source_msg.text, Config.OFFSET)
            await client.send_message(
                chat_id=target_chat_id,
                text=modified_text,
                parse_mode=ParseMode.MARKDOWN
            )
        return True
        
    except FloodWait as e:
        print(f"Waiting {e.value} seconds due to flood limit")
        await asyncio.sleep(e.value)
        return False
    except Exception as e:
        print(f"Error processing message {source_msg.id}: {e}")
        return False

@app.on_message(filters.command(["start", "help"]))
async def start_cmd(client: Client, message: Message):
    help_text = """
🤖 **Batch Link Modifier Bot**

🔹 /batch - Process all posts between two links
🔹 /addnumber N - Add N to message IDs in captions
🔹 /lessnumber N - Subtract N from message IDs
🔹 /setoffset N - Set absolute offset value
🔹 /cancel - Stop current processing

**How to use batch mode:**
1. Set offset if needed
2. Send /batch
3. Send starting post link (e.g. https://t.me/channel/123)
4. Send ending post link (e.g. https://t.me/channel/456)

The bot will process all posts between these two IDs.
"""
    await message.reply(help_text)

@app.on_message(filters.command(["addnumber", "lessnumber", "setoffset"]))
async def set_offset_cmd(client: Client, message: Message):
    try:
        amount = int(message.command[1])
        if message.command[0] == "addnumber":
            Config.OFFSET += amount
            action = "Added"
        elif message.command[0] == "lessnumber":
            Config.OFFSET -= amount
            action = "Subtracted"
        else:
            Config.OFFSET = amount
            action = "Set"
        
        await message.reply(f"✅ {action} offset: {amount}\nNew offset: {Config.OFFSET}")
    except:
        await message.reply("⚠️ Usage: /addnumber 2 or /lessnumber 3 or /setoffset 5")

@app.on_message(filters.command("batch"))
async def start_batch(client: Client, message: Message):
    if Config.PROCESSING:
        return await message.reply("⚠️ Already processing, use /cancel to stop")
    
    Config.PROCESSING = True
    Config.BATCH_MODE = True
    Config.CHAT_ID = None
    Config.START_ID = None
    Config.END_ID = None
    
    await message.reply(
        f"🔹 Batch Mode Started\n"
        f"🔢 Current Offset: {Config.OFFSET}\n\n"
        f"Please send the STARTING post link\n"
        f"(e.g. https://t.me/channel/123)"
    )

@app.on_message(filters.command("cancel"))
async def cancel_cmd(client: Client, message: Message):
    Config.PROCESSING = False
    Config.BATCH_MODE = False
    await message.reply("✅ Processing stopped")

@app.on_message(filters.text & filters.create(is_not_command))
async def handle_message(client: Client, message: Message):
    if not Config.PROCESSING or "t.me/" not in message.text:
        return
    
    try:
        match = re.search(r't\.me/(?:c/)?([^/]+)/(\d+)', message.text)
        if not match:
            return await message.reply("❌ Invalid link format. Send like: https://t.me/channel/123")

        chat_id = match.group(1)
        msg_id = int(match.group(2))

        if Config.BATCH_MODE:
            if Config.START_ID is None:
                Config.START_ID = msg_id
                Config.CHAT_ID = chat_id
                await message.reply(
                    f"✅ Starting point set: {msg_id}\n"
                    f"Now send the ENDING post link\n"
                    f"(e.g. https://t.me/channel/456)"
                )
            elif Config.END_ID is None:
                if chat_id != Config.CHAT_ID:
                    return await message.reply("❌ Both links must be from same channel")
                
                Config.END_ID = msg_id
                await process_batch(client, message)
        else:
            # Single post processing
            msg = await client.get_messages(chat_id, msg_id)
            if not msg:
                return await message.reply("❌ Couldn't fetch that message")
            
            await process_message(client, msg, message.chat.id)
            
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
        Config.PROCESSING = False
        Config.BATCH_MODE = False

async def process_batch(client: Client, message: Message):
    try:
        start_id = min(Config.START_ID, Config.END_ID)
        end_id = max(Config.START_ID, Config.END_ID)
        total = end_id - start_id + 1
        
        progress_msg = await message.reply(
            f"⏳ Starting batch processing\n"
            f"From ID: {start_id} to {end_id}\n"
            f"Total posts: {total}\n"
            f"Offset: {Config.OFFSET}"
        )
        
        processed = failed = 0
        
        for current_id in range(start_id, end_id + 1):
            if not Config.PROCESSING:
                break
            
            try:
                msg = await client.get_messages(Config.CHAT_ID, current_id)
                if msg and not msg.empty:
                    success = await process_message(client, msg, message.chat.id)
                    if success:
                        processed += 1
                    else:
                        failed += 1
                
                if (processed + failed) % 5 == 0 or current_id == end_id:
                    await progress_msg.edit(
                        f"⏳ Processing: {current_id}/{end_id}\n"
                        f"✅ Success: {processed}\n"
                        f"❌ Failed: {failed}\n"
                        f"📶 Progress: {((current_id-start_id)/total)*100:.1f}%"
                    )
                
                await asyncio.sleep(1)
            
            except FloodWait as e:
                await asyncio.sleep(e.value)
                failed += 1
            except Exception as e:
                print(f"Error processing {current_id}: {e}")
                failed += 1
        
        await progress_msg.edit(
            f"✅ Batch Complete!\n"
            f"• Total Processed: {processed}\n"
            f"• Failed: {failed}\n"
            f"• Offset Applied: {Config.OFFSET}"
        )
    
    except Exception as e:
        await message.reply(f"❌ Batch Error: {str(e)}")
    finally:
        Config.PROCESSING = False
        Config.BATCH_MODE = False

if __name__ == "__main__":
    print("⚡ Batch Link Modifier Bot Started!")
    app.start()
    idle()
    app.stop()
