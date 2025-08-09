
import os
import sys
import asyncio
from typing import List

# Ensure current directory is on the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import discord
from discord.ext import commands
from discord import app_commands

from core.config import load_config
from core.logger import log
# orders helpers are imported for side effects / use by cogs
from core.orders import orders, save_orders, generate_order_id  # noqa: F401

# -----------------------------
# Configuration
# -----------------------------
config = load_config()
TOKEN = config.get("TOKEN")
GUILD_ID_RAW = config.get("GUILD_ID")

if not TOKEN:
    raise RuntimeError("Missing TOKEN in config")
if not GUILD_ID_RAW:
    raise RuntimeError("Missing GUILD_ID in config")

GUILD_ID = int(GUILD_ID_RAW)
PREFIX = config.get("PREFIX", "!")

# -----------------------------
# Bot setup
# -----------------------------
intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
)

print(">>> Đã tạo bot, chuẩn bị khởi động…")
log("Bot instance created; preparing to start…")


async def _print_registered_commands(cmds: List[app_commands.AppCommand]) -> None:
    print(f"Các lệnh đã đăng ký ({len(cmds)}):")
    for cmd in cmds:
        # name and description are safe attributes for all app commands
        print(f"  /{cmd.name} - {cmd.description}")


@bot.event
async def on_ready():
    """Runs once the bot is fully connected."""
    try:
        if not bot.user:
            print("❌ Bot user is not available yet.")
            return

        print(f"✅ Bot đã đăng nhập với tên: {bot.user.name}")
        print(f"✅ Bot ID: {bot.user.id}")
        print(f"✅ Server ID mục tiêu (sync): {GUILD_ID}")

        # List servers the bot is currently in
        guilds = bot.guilds
        print(f"Bot đang ở trong {len(guilds)} server:")
        for guild in guilds:
            print(f"  - {guild.name} (ID: {guild.id})")

        # Show the currently cached commands
        await _print_registered_commands(bot.tree.get_commands())

    except Exception as e:
        print(f"❌ Lỗi khi khởi động bot: {e}")
        import traceback
        traceback.print_exc()
        return

    log("Bot đã sẵn sàng.")

    # Start background order monitoring task (if available)
    try:
        from tasks.order_monitor import don_giam_sat  # imported here to avoid import at module load
        # Prefer asyncio.create_task over the deprecated loop.create_task
        asyncio.create_task(don_giam_sat(bot))
        print("✅ Đã khởi động giám sát đơn hàng")
    except Exception as e:
        print(f"❌ Lỗi khi khởi động giám sát: {e}")


@bot.event
async def setup_hook():
    """Discord.py 2.x lifecycle hook for async setup before connecting."""
    try:
        print("[Setup] Đang tải extensions…")

        # Load cogs/extensions
        await bot.load_extension("cogs.order_commands")
        print("[Setup] Đã tải order_commands thành công")

        print("[Setup] Đang đồng bộ lệnh…")
        guild_obj = discord.Object(id=GUILD_ID)

        # Clear and resync only for the target guild for faster iteration
        print("[Setup] Xóa lệnh cũ ở guild mục tiêu…")
        bot.tree.clear_commands(guild=guild_obj)

        # First, ensure global cache is up-to-date (optional but harmless)
        await bot.tree.sync(guild=None)

        print("[Setup] Đồng bộ lệnh mới cho guild mục tiêu…")
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"[Setup] Đã đồng bộ {len(synced)} lệnh cho server {GUILD_ID}")

        if len(synced) == 0:
            print("⚠️ CẢNH BÁO: Không có lệnh nào được đồng bộ!")
            print("👉 Kiểm tra:")
            print("  1. Bot có quyền applications.commands")
            print("  2. GUILD_ID đúng")
            print("  3. Bot đã được mời với đủ scope")
            print("  4. Cogs đã được tải đúng")
            print("  5. Các intents đã được bật")

    except Exception as e:
        print(f"❌ Lỗi trong setup_hook: {e}")
        import traceback
        traceback.print_exc()


# -----------------------------
# App command error handling
# -----------------------------
@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    try:
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏳ Vui lòng đợi {error.retry_after:.2f} giây nữa.",
                ephemeral=True,
            )
            return

        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "⛔ Bạn không có quyền sử dụng lệnh này!",
                ephemeral=True,
            )
            return

        # Fallback: log and notify user
        print(f"Lỗi khi thực thi lệnh: {str(error)}")
        if interaction.response.is_done():
            # Followup if an initial response already happened
            await interaction.followup.send(
                "❌ Đã xảy ra lỗi khi thực thi lệnh.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Đã xảy ra lỗi khi thực thi lệnh.", ephemeral=True
            )

    except Exception as inner:
        # Last-resort logging to avoid swallowing exceptions
        print(f"❌ Lỗi trong error handler: {inner}")


print(">>> Bot đã sẵn sàng, đang khởi động…")
bot.run(TOKEN)