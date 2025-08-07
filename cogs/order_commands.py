import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import os
import sys

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import from core as a package
from core import orders, save_orders, generate_order_id, log

class DonHang(discord.ui.Modal, title="Đặt đơn Cave Store"):
    def __init__(self):
        super().__init__()
        self.hinh_thuc = discord.ui.TextInput(label="Hình thức (SL/RP/Event/Modul)", required=True)
        self.loai      = discord.ui.TextInput(label="Loại (Tank/Air/Heli/Ship hoặc Task/CP)", required=False)
        self.so_luong  = discord.ui.TextInput(label="Số lượng", required=False)
        self.ghi_chu   = discord.ui.TextInput(label="Ghi chú thêm", style=discord.TextStyle.paragraph, required=False)
        for it in (self.hinh_thuc, self.loai, self.so_luong, self.ghi_chu):
            self.add_item(it)

    async def on_submit(self, interaction: discord.Interaction):
        user   = interaction.user
        ma_don = generate_order_id()
        orders[ma_don] = {
            "user": f"{user.name}#{user.discriminator}",
            "user_id": user.id,
            "hinh_thuc": self.hinh_thuc.value,
            "loai": self.loai.value,
            "so_luong": self.so_luong.value,
            "ghi_chu": self.ghi_chu.value,
            "trang_thai": "⏳ Chờ duyệt",
            "nguoi_nhan": None,
            "nguoi_nhan_id": None,
            "thoi_han": None,
            "thoi_gian": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "da_nhac_het_gio": False,
            "qua_han": False
        }
        save_orders()
        embed = discord.Embed(title="📥 Đơn hàng mới", color=0x00ffcc)
        embed.add_field(name="Mã đơn", value=f"`{ma_don}`", inline=True)
        embed.add_field(name="Khách",      value=user.mention, inline=True)
        embed.add_field(name="Hình thức",  value=self.hinh_thuc.value, inline=False)
        if self.loai.value:     embed.add_field(name="Loại",      value=self.loai.value, inline=True)
        if self.so_luong.value: embed.add_field(name="Số lượng",  value=self.so_luong.value, inline=True)
        if self.ghi_chu.value:  embed.add_field(name="Ghi chú",   value=self.ghi_chu.value, inline=False)
        embed.set_footer(text="Đơn đang chờ duyệt...")
        
        # Import locally to avoid circular imports
        from core import load_config
        config = load_config()
        for cid in (int(config["LOG_CHANNEL_ID"]), int(config["ADMIN_CHANNEL_ID"])):
            ch = interaction.client.get_channel(cid)
            if ch: 
                await ch.send(embed=embed)
            else:
                log(f"⚠️ Không tìm thấy kênh {cid}")
        log(f"[ĐƠN MỚI] {ma_don} từ {user}")
        await interaction.response.send_message(f"✅ Đã gửi đơn `{ma_don}`!", ephemeral=True)

class OrderCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Import config with correct path
        from core.config import load_config
        self.config = load_config()
        self.guild_obj = discord.Object(id=int(self.config["GUILD_ID"]))
        self.admin_ids = [int(id) for id in self.config["ADMIN_ID"]]

    @app_commands.command(name="donhang", description="Mở form để đặt đơn hàng mới")
    async def donhang(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DonHang())

    @app_commands.command(name="duyetdon", description="✅ Duyệt đơn hàng")
    @app_commands.describe(ma_don="Mã đơn cần duyệt")
    async def duyetdon(self, interaction: discord.Interaction, ma_don: str):
        if interaction.user.id not in self.admin_ids:
            return await interaction.response.send_message("⛔ Không có quyền!", ephemeral=True)
        if ma_don not in orders:
            return await interaction.response.send_message("❌ Không tìm thấy đơn.", ephemeral=True)
        orders[ma_don]["trang_thai"] = "✅ Đã duyệt"
        save_orders()
        try:
            u = await self.bot.fetch_user(orders[ma_don]["user_id"])
            await u.send(f"📢 Đơn `{ma_don}` đã được duyệt.")
        except: 
            log(f"⚠️ Không thể gửi DM cho user {orders[ma_don]['user_id']}")
        log(f"[DUYỆT] {ma_don} bởi {interaction.user}")
        await interaction.response.send_message(f"✅ Đã duyệt `{ma_don}`", ephemeral=True)

    @app_commands.command(name="trangthai", description="🔍 Xem trạng thái đơn")
    @app_commands.describe(ma_don="Mã đơn")
    async def trangthai(self, interaction: discord.Interaction, ma_don: str):
        if ma_don not in orders:
            return await interaction.response.send_message("❌ Không tìm thấy đơn.", ephemeral=True)
        o = orders[ma_don]
        try:
            e = discord.Embed(title=f"📦 Đơn `{ma_don}`", color=0x00ffcc)
            e.add_field(name="👤 Khách",       value=f"<@{o['user_id']}>", inline=True)
            e.add_field(name="📦 Hình thức",   value=o["hinh_thuc"], inline=True)
            if o.get("loai"):     e.add_field(name="📚 Loại",     value=o["loai"],     inline=True)
            if o.get("so_luong"): e.add_field(name="🔢 Số lượng", value=o["so_luong"], inline=True)
            if o.get("ghi_chu"):  e.add_field(name="📝 Ghi chú",  value=o["ghi_chu"],  inline=False)
            e.add_field(name="📌 Trạng thái", value=o["trang_thai"], inline=False)
            if o.get("nguoi_nhan_id"): e.add_field(name="⚙️ Người nhận", value=f"<@{o['nguoi_nhan_id']}>", inline=False)
            if o.get("thoi_han"):      e.add_field(name="⏳ Hạn chót",    value=o["thoi_han"], inline=False)
            if o.get("thoi_gian"):     e.set_footer(text=f"🕒 Đặt lúc: {o['thoi_gian']}")
            await interaction.response.send_message(embed=e, ephemeral=True)
        except Exception as err:
            await interaction.response.send_message(f"❌ Lỗi khi hiển thị đơn: {err}", ephemeral=True)

    @app_commands.command(name="huydon", description="❌ Huỷ đơn của bạn")
    @app_commands.describe(ma_don="Mã đơn")
    async def huydon(self, interaction: discord.Interaction, ma_don: str):
        if ma_don not in orders:
            return await interaction.response.send_message("❌ Không tìm thấy đơn.", ephemeral=True)
        if interaction.user.id != orders[ma_don]["user_id"]:
            return await interaction.response.send_message("⛔ Không thể huỷ đơn của người khác.", ephemeral=True)
        if orders[ma_don]["trang_thai"] != "⏳ Chờ duyệt":
            return await interaction.response.send_message("❌ Đơn đã được duyệt, không thể huỷ.", ephemeral=True)
        del orders[ma_don]; save_orders()
        log(f"[HUỶ] {ma_don} bởi {interaction.user}")
        await interaction.response.send_message(f"✅ Đã huỷ `{ma_don}`", ephemeral=True)

    @app_commands.command(name="nhancay", description="📥 Nhận đơn (chốt đơn)")
    @app_commands.describe(ma_don="Mã đơn", thoi_han="Thời hạn hoàn thành (giờ)")
    async def nhancay(self, interaction: discord.Interaction, ma_don: str, thoi_han: int):
        # Defer the response immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate order exists
            if ma_don not in orders:
                await interaction.followup.send("❌ Không tìm thấy đơn.", ephemeral=True)
                return

            # Check if order is already taken
            if orders[ma_don].get("nguoi_nhan_id"):
                await interaction.followup.send("⛔ Đơn đã có người nhận.", ephemeral=True)
                return

            # Process the order
            u = interaction.user
            deadline_dt = datetime.now(timezone.utc) + timedelta(hours=thoi_han)
            han_chot_str = deadline_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Update order info
            orders[ma_don].update({
                "nguoi_nhan": f"{u.name}#{u.discriminator}",
                "nguoi_nhan_id": u.id,
                "trang_thai": "🚀 Đang xử lý",
                "thoi_han": han_chot_str,
                "da_nhac_het_gio": False,
                "qua_han": False
            })
            
            # Save changes
            save_orders()
            log(f"[NHẬN] {ma_don} bởi {u.name}#{u.discriminator}")
            
            # Send success message
            await interaction.followup.send(
                f"✅ Bạn đã nhận `{ma_don}`. Hoàn thành trong {thoi_han}h (đến {han_chot_str}).",
                ephemeral=True
            )
            
        except Exception as e:
            log(f"[LỖI] Trong lệnh /nhancay: {e}")
            await interaction.followup.send("🚨 Đã xảy ra lỗi khi nhận đơn.", ephemeral=True)

    @app_commands.command(name="hoanthanh", description="🎉 Đánh dấu hoàn thành")
    @app_commands.describe(ma_don="Mã đơn")
    async def hoanthanh(self, interaction: discord.Interaction, ma_don: str):
        if ma_don not in orders:
            return await interaction.response.send_message("❌ Không tìm thấy.", ephemeral=True)
        if orders[ma_don]["nguoi_nhan_id"] != interaction.user.id:
            return await interaction.response.send_message("⛔ Bạn không nhận đơn này.", ephemeral=True)
        orders[ma_don]["trang_thai"] = "✅ Đã hoàn thành"
        save_orders()
        log(f"[HOÀN THÀNH] {ma_don} bởi {interaction.user}")
        await interaction.response.send_message(f"✅ Hoàn thành `{ma_don}`!", ephemeral=True)

    @app_commands.command(name="suadon", description="✏️ Chỉnh sửa ghi chú đơn")
    @app_commands.describe(ma_don="Mã đơn", ghichu="Ghi chú mới")
    async def suadon(self, interaction: discord.Interaction, ma_don: str, ghichu: str):
        if ma_don not in orders:
            return await interaction.response.send_message("❌ Không tìm thấy.", ephemeral=True)
        if interaction.user.id not in (*self.admin_ids, orders[ma_don]["user_id"]):
            return await interaction.response.send_message("⛔ Không có quyền.", ephemeral=True)
        orders[ma_don]["ghi_chu"] = ghichu
        save_orders()
        log(f"[SỬA] {ma_don} ghi chú -> {ghichu}")
        await interaction.response.send_message(f"✅ Đã cập nhật ghi chú cho `{ma_don}`", ephemeral=True)

    @app_commands.command(name="xoadon", description="🗑️ Xoá đơn (Admin)")
    @app_commands.describe(ma_don="Mã đơn")
    async def xoadon(self, interaction: discord.Interaction, ma_don: str):
        if interaction.user.id not in self.admin_ids:
            return await interaction.response.send_message("⛔ Không có quyền!", ephemeral=True)
        if ma_don not in orders:
            return await interaction.response.send_message("❌ Không tồn tại.", ephemeral=True)
        del orders[ma_don]; save_orders()
        log(f"[XOÁ] {ma_don} bởi {interaction.user}")
        await interaction.response.send_message(f"🗑️ Đã xóa `{ma_don}`", ephemeral=True)

    @app_commands.command(name="giahan", description="🕒 Gia hạn thời gian cày")
    @app_commands.describe(ma_don="Mã đơn", so_phut="Số phút thêm")
    async def giahan(self, interaction: discord.Interaction, ma_don: str, so_phut: int):
        if ma_don not in orders:
            return await interaction.response.send_message("❌ Không tìm thấy.", ephemeral=True)
        don = orders[ma_don]
        if not don.get("nguoi_nhan_id"):
            return await interaction.response.send_message("⚠️ Chưa nhận.", ephemeral=True)
        try:
            old_str = don["thoi_han"]
            if " UTC" not in old_str:
                old_str += " UTC"
            old = datetime.strptime(old_str, "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=timezone.utc)
            new = old + timedelta(minutes=so_phut)
            new_str = new.strftime("%Y-%m-%d %H:%M:%S UTC")
            don["thoi_han"] = new_str
            don["da_nhac_het_gio"] = False
            don["qua_han"] = False
            save_orders()
            log(f"[GIA HẠN] {ma_don} +{so_phut}m -> {don['thoi_han']}")
            try:
                await self.bot.fetch_user(don["nguoi_nhan_id"]).send(
                    f"📌 `{ma_don}` được gia hạn +{so_phut} phút. Hạn: {don['thoi_han']}")
            except:
                log(f"[LỖI] Không thể gửi DM cho người nhận đơn {ma_don}")
            await interaction.response.send_message("✅ Gia hạn thành công.", ephemeral=True)
        except Exception as e:
            log(f"[ERR] giahan {ma_don}: {e}")
            await interaction.response.send_message("❌ Lỗi khi gia hạn.", ephemeral=True)

    @app_commands.command(name="tinhgia", description="💰 Tính giá trị đơn hàng")
    @app_commands.describe(hinh_thuc="SL/RP/Event/Modul", loai="Loại", so_luong="Số lượng", premium="RP premium? yes/no")
    async def tinhgia(self, interaction: discord.Interaction, hinh_thuc: str, loai: str="", so_luong: str="1", premium: str="yes"):
        try:
            H, L, S, P = hinh_thuc.upper(), loai.upper(), int(''.join(filter(str.isdigit, so_luong)) or 1), premium.lower()
            if H=="SL": price=(S/1_000_000)*100_000
            elif H=="RP": price=(S/100_000)*(120_000 if P=="yes" else 140_000)
            elif H=="EVENT": price=S*650_000
            elif H=="MODUL":
                if L in ("TANK","AIR"): price=S*300_000
                elif L=="HELI": price=S*375_000
                elif L=="SHIP": price=S*400_000
                else: return await interaction.response.send_message("❌ Loại Modul sai.", ephemeral=True)
            else:
                return await interaction.response.send_message("❌ Hình thức sai.", ephemeral=True)
            await interaction.response.send_message(f"💸 Giá: **{int(price):,} VNĐ**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)

    @app_commands.command(name="thongke", description="📈 Thống kê đơn hàng")
    async def thongke(self, interaction: discord.Interaction):
        done = sum(1 for o in orders.values() if o["trang_thai"]=="✅ Đã hoàn thành")
        late = sum(1 for o in orders.values() if o["trang_thai"]=="⚠️ Quá hạn")
        processing = sum(1 for o in orders.values() if o["trang_thai"]=="🚀 Đang xử lý")
        await interaction.response.send_message(
            f"📦 Tổng đơn: `{len(orders)}`\n"
            f"✅ Hoàn thành: `{done}`\n"
            f"🚀 Đang xử lý: `{processing}`\n"
            f"⏰ Quá hạn: `{late}`",
            ephemeral=True
        )

    @app_commands.command(name="danhsachdon", description="📋 Xem danh sách đơn hàng")
    @app_commands.describe(trang_thai="Lọc theo trạng thái (vd: 'Chờ duyệt')")
    async def danhsachdon(self, interaction: discord.Interaction, trang_thai: str = None):
        try:
            filtered = []
            for mid, o in orders.items():
                if trang_thai is None or o['trang_thai'] == trang_thai:
                    filtered.append((mid, o))
            if not filtered:
                return await interaction.response.send_message("❌ Không có đơn nào phù hợp", ephemeral=True)
            filtered.sort(key=lambda x: x[1]['thoi_gian'], reverse=True)
            filtered = filtered[:10]
            embed = discord.Embed(title="📋 Danh sách đơn hàng", color=0x3498db)
            for mid, o in filtered:
                status = o['trang_thai']
                customer = o['user']
                embed.add_field(
                    name=f"`{mid}` - {status}",
                    value=f"👤 {customer}\n⏰ {o['thoi_gian']}",
                    inline=False
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            log(f"[LỖI] danhsachdon: {e}")
            await interaction.response.send_message("❌ Đã xảy ra lỗi khi lấy danh sách", ephemeral=True)

async def setup(bot):
    await bot.add_cog(OrderCommands(bot))
    print(f"[SETUP] OrderCommands cog loaded successfully with {len(bot.tree.get_commands())} commands")
