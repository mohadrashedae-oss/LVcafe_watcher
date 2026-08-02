import os
import requests

# جلب المفاتيح السرية من GitHub Secrets
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# إعدادات الفحص
VENUE_SLUG = "lecafelouisvuitton"
PARTY_SIZE = 3
START_DATE = "2026-08-11"
END_DATE = "2026-08-18"

def send_telegram(message, target_chat_id=None):
    if not target_chat_id:
        target_chat_id = CHAT_ID
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"فشل إرسال رسالة تيليجرام: {e}")

def check_for_start_command():
    """قراءة كل الرسائل المعلقة والرد فوراً على أي شخص أرسل /start"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url, timeout=10).json()
        if response.get("ok"):
            results = response.get("result", [])
            for result in results:
                message = result.get("message", {})
                text = message.get("text", "")
                user_chat_id = message.get("chat", {}).get("id")
                update_id = result.get("update_id")

                # التحقق من أمر /start
                if text and "/start" in text and user_chat_id:
                    welcome_msg = (
                        "🟢 **البوت يعمل بنجاح!**\n\n"
                        "تم تفعيل المراقبة، وسيتم إشعارك فوراً في حال توفر أي حجز خلال الفترة من **11 إلى 18 أغسطس**! ☕️👜✨"
                    )
                    send_telegram(welcome_msg, target_chat_id=user_chat_id)
                
                # تأكيد معالجة الرسالة حتى لا تتكرر
                requests.get(f"{url}?offset={update_id + 1}", timeout=5)
    except Exception as e:
        print(f"خطأ أثناء قراءة الرسائل الواردة: {e}")

def check_availability():
    # 1. الرد على أي شخص أرسل /start مؤخراً
    check_for_start_command()

    # 2. رابط API الخاص بـ SevenRooms
    url = f"https://www.sevenrooms.com/api-yoog/availability/widget/range?venue={VENUE_SLUG}&party_size={PARTY_SIZE}&start_date={START_DATE}&end_date={END_DATE}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"خطأ في الاتصال بالخادم: {response.status_code}")
            return

        data = response.json()
        available_slots = []

        # تحليل المواعيد المتاحة
        availability = data.get("data", {}).get("availability", {})
        for date, slots in availability.items():
            for slot in slots:
                if slot.get("timeslot_type") == "available":
                    time_str = slot.get("time")
                    available_slots.append(f"📅 **{date}**  ⏱️ **{time_str}**")

        # في حال توفر موعد -> تنبيه حجز فوري 🚨
        if available_slots:
            msg = f"🚨 **تنبيه توفر مواعيد في Le Café Louis Vuitton بانكوك!** 🇹🇭\n\n"
            msg += f"👥 **عدد الأشخاص:** {PARTY_SIZE}\n\n"
            msg += "\n".join(available_slots)
            msg += f"\n\n🔗 [اضغط هنا للحجز الفوري](https://www.sevenrooms.com/reservations/{VENUE_SLUG})"
            send_telegram(msg)
            print("✅ تم العثور على مواعيد وإرسال التنبيه!")

        # في حال عدم توفر موعد -> إشعار طمأنة دوري 🙂
        else:
            status_msg = "لا تحاتي الغالي قاعدين ندور لك حجز 🙂"
            send_telegram(status_msg)
            print("تم إرسال رسالة الطمأنة إلى تيليجرام.")

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {e}")

if __name__ == "__main__":
    check_availability()
