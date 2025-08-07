

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import discord
from discord.ext import commands
from discord import app_commands
from core.config import load_config
from core.logger import log
from core.orders import orders, save_orders, generate_order_id

# Load config
config = load_config()
TOKEN = config["TOKEN"]
GUILD_ID = int(config["GUILD_ID"])

# Set up intents
intents = discord.Intents.all()  # Enable all intents

bot = commands.Bot(
    command_prefix=config.get("PREFIX", "!"),
    intents=intents,
    help_command=None
)

print(">>> Đã tạo bot, chuẩn bị khởi động,hehe...")


@bot.event
async def on_ready():
    try:
        print(f"✅ Bot đã đăng nhập với tên: {bot.user.name}")
        print(f"✅ Bot ID: {bot.user.id}")
        print(f"✅ Server ID: {GUILD_ID}")
        
        # Print all servers the bot is in
        guilds = bot.guilds
        print(f"Bot đang ở trong {len(guilds)} server:")
        for guild in guilds:
            print(f"  - {guild.name} (ID: {guild.id})")
            
        # Print all registered commands
        commands = bot.tree.get_commands()
        print(f"Các lệnh đã đăng ký ({len(commands)}):")
        for cmd in commands:
            print(f"  /{cmd.name} - {cmd.description}")
            
    except Exception as e:
        print(f"❌ Lỗi khi khởi động bot: {e}")
        import traceback
        traceback.print_exc()
        return
        
    log("Bot đã sẵn sàng.")
    
    # Start order monitoring task
    try:
        from tasks.order_monitor import don_giam_sat
        bot.loop.create_task(don_giam_sat(bot))
        print("✅ Đã khởi động giám sát đơn hàng")
    except Exception as e:
        print(f"❌ Lỗi khi khởi động giám sát: {e}")






# Load cogs and sync commands
@bot.event
async def setup_hook():
    try:
        print("[Setup] Đang tải extensions...")
        
        # Load order commands
        await bot.load_extension("cogs.order_commands")
        print("[Setup] Đã tải order_commands thành công")
        
        print("[Setup] Đang đồng bộ lệnh...")
        guild = discord.Object(id=GUILD_ID)
        
        # Clear and sync commands
        print("[Setup] Xóa lệnh cũ...")
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=None)  # Sync globally first
        
        print("[Setup] Đồng bộ lệnh mới...")
        commands = await bot.tree.sync(guild=guild)
        print(f"[Setup] Đã đồng bộ {len(commands)} lệnh cho server")
        
        # Show warning if no commands were synced
        if len(commands) == 0:
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

# Error handler for slash commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏳ Vui lòng đợi {error.retry_after:.2f} giây nữa.",
            ephemeral=True
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "⛔ Bạn không có quyền sử dụng lệnh này!",
            ephemeral=True
        )
    else:
        print(f"Lỗi khi thực thi lệnh: {str(error)}")
        await interaction.response.send_message(
            "❌ Đã xảy ra lỗi khi thực thi lệnh.",
            ephemeral=True
        )

print(">>> Bot đã sẵn sàng, đang khởi động...")
bot.run(TOKEN)