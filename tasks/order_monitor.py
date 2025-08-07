import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from datetime import datetime, timezone
from core.orders import orders, save_orders
from core.logger import log
from core.config import load_config
import discord

async def don_giam_sat(bot):
    config = load_config()
    NOTIFY_CHANNEL_ID = int(config["NOTIFY_CHANNEL_ID"])
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            now = datetime.now(timezone.utc)
            notif_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
            for mid, o in list(orders.items()):
                try:
                    if not o.get("thoi_han") or not o.get("nguoi_nhan_id"):
                        continue
                    deadline_str = o["thoi_han"]
                    if " UTC" not in deadline_str:
                        deadline_str += " UTC"
                    deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=timezone.utc)
                    time_left = (deadline - now).total_seconds()
                    if 0 < time_left <= 3600 and not o["da_nhac_het_gio"]:
                        try:
                            user = await bot.fetch_user(o["nguoi_nhan_id"])
                            mins_left = int(time_left // 60)
                            await user.send(f"⏰ Đơn `{mid}` còn {mins_left} phút! Hãy hoàn thành sớm!")
                        except Exception as e:
                            log(f"[Cảnh báo] Không gửi được nhắc nhở cho {o['nguoi_nhan_id']}: {e}")
                        o["da_nhac_het_gio"] = True
                        save_orders()
                    elif time_left <= 0 and not o["qua_han"]:
                        o["trang_thai"] = "⚠️ Quá hạn"
                        o["qua_han"] = True
                        save_orders()
                        try:
                            user = await bot.fetch_user(o["nguoi_nhan_id"])
                            await user.send(f"❗ ĐƠN `{mid}` ĐÃ QUÁ HẠN! Vui lòng hoàn thành ngay!")
                        except:
                            log(f"[Cảnh báo] Không gửi được thông báo quá hạn cho {o['nguoi_nhan_id']}")
                        if notif_channel:
                            await notif_channel.send(
                                f"⏰ **THÔNG BÁO QUÁ HẠN**\n"
                                f"> Người nhận: <@{o['nguoi_nhan_id']}>\n"
                                f"> Mã đơn: `{mid}`\n"
                                f"> Khách hàng: <@{o['user_id']}>"
                            )
                except Exception as e:
                    log(f"[LỖI GIÁM SÁT] {mid}: {e}")
            await asyncio.sleep(60)
        except Exception as e:
            log(f"[LỖI NẶNG GIÁM SÁT] {e}")
            await asyncio.sleep(60)
