############################ ALL PLATFORM INC SPOTIFY ######################
#---------------------> INSTAGRAM IS NOT WORKING <-------------------------#
import os
import yt_dlp
import datetime
import logging
import subprocess

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

# Bot Token (secure): read from environment variable `TOKEN`
# Read TOKEN from environment for secure deployments
TOKEN = os.getenv("TOKEN")
if TOKEN:
    TOKEN = TOKEN.strip()  # Remove any whitespace/newlines


# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fail early if TOKEN not set
if not TOKEN:
    logger.error("Bot TOKEN not set. Set the `TOKEN` environment variable before running.")
    raise SystemExit("Missing TOKEN environment variable")

# ====== MAIN MENU ======

def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("Instagram", callback_data="instagram"),
            InlineKeyboardButton("YouTube", callback_data="youtube"),
        ],
        [
            InlineKeyboardButton("Twitter (X)", callback_data="twitter"),
            InlineKeyboardButton("Spotify 🎵", callback_data="spotify"),
        ],
        [InlineKeyboardButton("About Bot", callback_data="about_bot")],
    ]
    return InlineKeyboardMarkup(keyboard)


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Select a platform:", reply_markup=get_main_menu())


# ====== BUTTON CLICK HANDLER ======

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "instagram":
        await query.message.reply_text(
            "📥 Instagram Action:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Download Reel", callback_data="instagram_download")],
                    [InlineKeyboardButton("Extract Audio", callback_data="instagram_audio")],
                    [InlineKeyboardButton("View Info", callback_data="instagram_info")],
                ]
            ),
        )

    elif query.data == "youtube":
        await query.message.reply_text(
            "📥 YouTube Action:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Download Video", callback_data="youtube_download")],
                    [InlineKeyboardButton("Extract Audio", callback_data="youtube_audio")],
                    [InlineKeyboardButton("View Info", callback_data="youtube_info")],
                ]
            ),
        )

    elif query.data == "twitter":
        await query.message.reply_text(
            "📥 Twitter (X) Action:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Download Video", callback_data="twitter_download")],
                    [InlineKeyboardButton("View Info", callback_data="twitter_info")],
                ]
            ),
        )

    elif query.data == "spotify":
        await query.message.reply_text(
            "🎵 Spotify Action:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Download Song (MP3)", callback_data="spotify_download")],
                ]
            ),
        )

    elif query.data == "about_bot":
        await query.message.reply_text(
            "🤖 I help you download videos or extract audio from:\n"
            "• Instagram\n• YouTube\n• Twitter (X)\n• Spotify (songs)\n\n"
            "Select a platform using /start and send a link!"
        )


# ====== PLATFORM SUBMENU ACTIONS ======

async def instagram_action_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["platform_action"] = update.callback_query.data
    await update.callback_query.message.reply_text("📥 Send Instagram link.")


async def youtube_action_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["platform_action"] = update.callback_query.data
    await update.callback_query.message.reply_text("📥 Send YouTube link.")


async def twitter_action_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["platform_action"] = update.callback_query.data
    await update.callback_query.message.reply_text("📥 Send Twitter (X) link.")


async def spotify_action_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["platform_action"] = update.callback_query.data  # "spotify_download"
    await update.callback_query.message.reply_text("🎵 Send Spotify song link.")


# ====== INFO + THUMBNAIL (YT/IG/TWITTER ONLY) ======

def get_video_info_and_thumbnail(url):
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get("title", "N/A")
        uploader = info.get("uploader", "Unknown uploader")
        upload_date = info.get("upload_date", "")
        if upload_date:
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
        duration = str(datetime.timedelta(seconds=info.get("duration", 0)))
        description = info.get("description", "")
        if description and len(description) > 300:
            description = description[:300] + "..."

        caption = (
            f"*Title:* {title}\n"
            f"*Uploader:* {uploader}\n"
            f"*Upload Date:* {upload_date}\n"
            f"*Duration:* {duration}\n"
            f"*Description:* {description}"
        )
        return escape_markdown(caption, version=2), info.get("thumbnail")

    except Exception as e:
        print("Info error:", e)
        return "⚠️ Could not fetch info.", None


# ====== DOWNLOAD MEDIA (IG/YT/TWITTER) ======

def download_media(url, mode="video"):
    try:
        os.makedirs("Downloads", exist_ok=True)
        opts = {
            "outtmpl": os.path.join("Downloads", "%(title)s.%(ext)s"),
            "format": "bestaudio/best" if mode == "audio" else "bestvideo+bestaudio/best",
        }
        if mode == "audio":
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }
            ]

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if mode == "audio":
                mp3_file = os.path.splitext(filename)[0] + ".mp3"
                return mp3_file if os.path.exists(mp3_file) else filename
            return filename

    except Exception as e:
        print("Download error:", e)
        return None


# ====== DOWNLOAD SPOTIFY SONG (SPOTDL) ======

def download_spotify_song(url: str, user_id: int) -> str | None:
    """
    Uses 'spotdl' CLI to download a Spotify track as mp3.
    Returns path to the mp3 file or None on failure.
    """
    try:
        base_folder = os.path.join("Downloads", "spotify", str(user_id))
        os.makedirs(base_folder, exist_ok=True)

        # Run spotdl command
        result = subprocess.run(
            ["spotdl", url, "--output", base_folder],
            capture_output=True,
            text=True,
        )

        logger.info("spotdl STDOUT:\n%s", result.stdout)
        if result.stderr:
            logger.warning("spotdl STDERR:\n%s", result.stderr)

        if result.returncode != 0:
            return None

        # Find the first mp3 file created in that folder
        for fname in os.listdir(base_folder):
            if fname.lower().endswith(".mp3"):
                return os.path.join(base_folder, fname)

        return None

    except Exception as e:
        logger.error("Spotify download error: %s", e)
        return None


# ====== URL HANDLER ======

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    loading = await update.message.reply_text("⏳ Processing...")
    action = context.user_data.get("platform_action")

    if not action:
        await loading.delete()
        await update.message.reply_text("❗ Please select a platform using /start.")
        return

    is_spotify = action.startswith("spotify_")

    # For non-Spotify platforms, pre-fetch info (unless it's an 'info' action)
    info = ""
    thumb = None
    if (not is_spotify) and ("info" not in action):
        info, _ = get_video_info_and_thumbnail(url)

    # ====== DOWNLOAD OR AUDIO ======
    if "download" in action or "audio" in action:
        # Spotify special case
        if is_spotify:
            # Basic validation
            if not url.startswith("https://open.spotify.com/"):
                await loading.delete()
                await update.message.reply_text("❌ Please send a valid *Spotify song link*.")
                return

            path = download_spotify_song(url, update.effective_user.id)
            await loading.delete()

            if path and os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        await update.message.reply_audio(
                            audio=f,
                            caption="✅ Spotify song downloaded.",
                        )
                    logger.info(f"Spotify audio sent successfully to user {update.effective_user.id}")
                except Exception as e:
                    logger.error(f"Failed to send Spotify audio: {e}")
                    await update.message.reply_text("⚠️ Failed to send audio. Please try again.")
                finally:
                    try:
                        os.remove(path)
                        logger.info(f"Deleted Spotify file from memory: {path}")
                    except Exception as e:
                        logger.warning(f"Could not delete Spotify file {path}: {e}")
            else:
                await update.message.reply_text("⚠️ Failed to download Spotify song. Please try another link.")

            return  # done for Spotify

        # ====== NORMAL IG/YT/TWITTER FLOW ======
        file_type = "audio" if "audio" in action else "video"
        path = download_media(url, file_type)
        await loading.delete()

        if path and os.path.exists(path):
            try:
                if file_type == "audio":
                    with open(path, "rb") as f:
                        await update.message.reply_audio(
                            audio=f,
                            caption=info,
                            parse_mode=ParseMode.MARKDOWN_V2,
                        )
                    logger.info(f"Audio file sent successfully to user {update.effective_user.id}")
                else:
                    with open(path, "rb") as f:
                        await update.message.reply_video(
                            video=f,
                            caption=info,
                            parse_mode=ParseMode.MARKDOWN_V2,
                        )
                    logger.info(f"Video file sent successfully to user {update.effective_user.id}")
            except Exception as e:
                logger.error(f"Failed to send {file_type}: {e}")
                await update.message.reply_text(f"⚠️ Failed to send {file_type}. Please try again.")
            finally:
                try:
                    os.remove(path)
                    logger.info(f"Deleted {file_type} file from memory: {path}")
                except Exception as e:
                    logger.warning(f"Could not delete {file_type} file {path}: {e}")
        else:
            await update.message.reply_text("⚠️ Failed to process media.")

    # ====== INFO ONLY ======
    elif "info" in action:
        await loading.delete()
        info, thumb = get_video_info_and_thumbnail(url)
        if thumb:
            await update.message.reply_photo(
                photo=thumb,
                caption=info,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        else:
            await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN_V2)

    else:
        await loading.delete()
        await update.message.reply_text("❗ Please select a platform using /start.")


# ====== MESSAGE HANDLER ======

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "http" in text:
        if context.user_data.get("platform_action"):
            await handle_url(update, context)
        else:
            await update.message.reply_text("📎 Please choose a platform using /start.")
    else:
        await update.message.reply_text("👋 Send me a media link after selecting a platform from /start.")


# ====== RUN THE BOT ======

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Main platform selection
    app.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern="^(instagram|youtube|twitter|spotify|about_bot)$",
        )
    )

    # Submenu actions
    app.add_handler(
        CallbackQueryHandler(
            instagram_action_selection,
            pattern="^instagram_(download|audio|info)$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            youtube_action_selection,
            pattern="^youtube_(download|audio|info)$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            twitter_action_selection,
            pattern="^twitter_(download|info)$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            spotify_action_selection,
            pattern="^spotify_(download)$",
        )
    )

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

    print("✅ Bot is running...")
    app.run_polling()