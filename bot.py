import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")          # Railway ENV variable se token
ADMIN_USERNAME = "nubcarder"        # lowercase rakho (safe)
DB_FILE = "data.json"

# ===== AUTO CREATE JSON =====
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

with open(DB_FILE, "r") as f:
    db = json.load(f)

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def is_admin(user):
    return user.username == ADMIN_USERNAME

def encode_text(text: str) -> str:
    return text.encode("utf-8").hex()

# ===== /start =====
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.args:
        code = ctx.args[0]
        if code in db:
            db[code]["hits"] += 1
            save_db()
            await update.message.reply_text(
                f"✅ Unlocked Successfully\n\n{db[code]['data']}"
            )
        else:
            await update.message.reply_text("❌ Invalid unlock code")
    else:
        await update.message.reply_text(
            "🔐 M3U Decoder Bot\n\n"
            "Paste your encoded code below 👇"
        )

# ===== /encode (ADMIN) =====
async def encode_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user):
        return
    ctx.user_data["mode"] = "encode"
    await update.message.reply_text("📥 Send text to encode:")

# ===== /stats =====
async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user):
        await update.message.reply_text(
            f"📊 Total stored codes: {len(db)}"
        )

# ===== SINGLE TEXT HANDLER (VERY IMPORTANT) =====
async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = msg.text.strip()

    # ---- ADMIN ENCODE MODE ----
    if is_admin(update.effective_user) and ctx.user_data.get("mode") == "encode":
        code = encode_text(text)

        if code not in db:
            db[code] = {
                "data": text,
                "hits": 0
            }
            save_db()

        ctx.user_data["mode"] = None
        await msg.reply_text(f"✅ Encoded Code:\n\n{code}")
        return

    # ---- PUBLIC DECODE ----
    if text in db:
        try:
            await msg.delete()  # encoded msg delete
        except:
            pass

        db[text]["hits"] += 1
        save_db()
        await ctx.bot.send_message(
            chat_id=msg.chat.id,
            text=f"✅ Unlocked Successfully\n\n{db[text]['data']}"
        )
        return

    # ---- INVALID TEXT ----
    await msg.reply_text("❌ Invalid or unknown code")

# ===== BOT START =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("encode", encode_cmd))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("✅ Bot is running...")
app.run_polling()
