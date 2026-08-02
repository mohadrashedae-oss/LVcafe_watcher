"""
مراقب حجوزات SevenRooms - LE CAFÉ LOUIS VUITTON
=================================================
يفحص نفس الـ API العام اللي يستخدمه موقع الحجز نفسه (نفس البيانات اللي
يشوفها أي زائر للصفحة)، ولو لقى أي وقت متاح بين التواريخ المحددة يرسل
لك تنبيه فوري على تيليجرام.

الإعداد قبل التشغيل
--------------------
1) ثبّت المكتبة المطلوبة:
   pip install requests

2) أنشئ بوت تيليجرام (دقيقتين):
   - افتح تيليجرام وابحث عن @BotFather
   - أرسل /newbot واتبع التعليمات، بيعطيك TOKEN
   - ابحث عن @userinfobot وأرسل له أي رسالة عشان يعطيك CHAT_ID الخاص فيك
   - عبّي القيمتين تحت في TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID

3) عدّل القيم في قسم CONFIG تحت حسب حاجتك (عدد الأشخاص، الفترة، إلخ)

4) شغّل السكريبت:
   python sevenrooms_watcher.py

   بيفضل شغال ويفحص كل POLL_INTERVAL_SECONDS، ويرسل لك تنبيه فور لقاء وقت فاضي.
"""

import requests
import time
import os
import logging
from datetime import date, timedelta

# ============== CONFIG - عدّل هذا القسم فقط ==============

VENUE = "lecafelouisvuitton"          # اسم المطعم في رابط الحجز
PARTY_SIZE = 3                         # عدد الأشخاص - غيّره حسب حاجتك

START_DATE = date(2026, 8, 11)         # أول تاريخ تبي تفحصه
END_DATE = date(2026, 8, 18)           # آخر تاريخ تبي تفحصه

# نقاط زمنية "مرساة" نفحص حولها عشان نغطي اليوم كامل (أي ساعة متاحة)
ANCHOR_TIMES = ["09:00", "12:00", "15:00", "18:00", "21:00"]
HALO_SIZE_INTERVAL = 16                # نطاق البحث حول كل نقطة (وحدة الموقع الداخلية)

# التوكن والـ chat ID ما يُكتبوا هنا — يُقرأوا من GitHub Secrets تلقائياً
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# =======================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.sevenrooms.com/api-yoa/availability/widget/range"
BOOKING_URL = f"https://www.sevenrooms.com/reservations/{VENUE}"


def send_telegram_alert(message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        if resp.status_code != 200:
            logger.error(f"فشل إرسال تنبيه تيليجرام: {resp.text}")
    except Exception as e:
        logger.error(f"خطأ أثناء إرسال تنبيه تيليجرام: {e}")


def check_date(check_date: date) -> set:
    """يفحص تاريخ واحد على عدة نقاط زمنية ويرجّع كل الأوقات المتاحة (بدون تكرار)."""
    found_times = set()
    date_str = check_date.strftime("%Y-%m-%d")

    for anchor in ANCHOR_TIMES:
        params = {
            "venue": VENUE,
            "time_slot": anchor,
            "party_size": PARTY_SIZE,
            "halo_size_interval": HALO_SIZE_INTERVAL,
            "start_date": date_str,
            "num_days": 1,
            "channel": "SEVENROOMS_WIDGET",
        }
        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            slots = data.get("data", {}).get("availability", {}).get(date_str, [])
            for slot_group in slots:
                for t in slot_group.get("times", []):
                    # نهتم فقط بالأوقات القابلة للحجز المباشر
                    if t.get("type") == "book":
                        found_times.add(t.get("time", "?"))
        except Exception as e:
            logger.warning(f"فشل الفحص لـ {date_str} عند {anchor}: {e}")

        time.sleep(1)  # فاصل بسيط بين الطلبات

    return found_times


def run():
    """فحصة واحدة كاملة لكل التواريخ، ثم يخرج. GitHub Actions يكرر التشغيل كل 5 دقائق."""
    logger.info("بدء الفحص...")
    logger.info(f"الفترة: {START_DATE} إلى {END_DATE} | عدد الأشخاص: {PARTY_SIZE}")

    d = START_DATE
    while d <= END_DATE:
        date_str = d.strftime("%Y-%m-%d")
        times = check_date(d)

        if times:
            message = (
                f"🎉 توفر حجز!\n"
                f"📅 التاريخ: {date_str}\n"
                f"🕐 الأوقات: {', '.join(sorted(times))}\n"
                f"👥 عدد الأشخاص: {PARTY_SIZE}\n"
                f"🔗 احجز الآن: {BOOKING_URL}"
            )
            logger.info(message)
            send_telegram_alert(message)
        else:
            logger.info(f"{date_str}: لا يوجد.")

        d += timedelta(days=1)

    logger.info("انتهى الفحص.")


if __name__ == "__main__":
    run()
