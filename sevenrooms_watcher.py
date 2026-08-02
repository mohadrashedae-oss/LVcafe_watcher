import os
import json
import requests

# جلب البيانات الحساسة من GitHub Secrets
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# إعدادات الحجز
VENUE_SLUG = "lecafelouisvuitton"
PARTY_SIZE = 3
START_DATE = "2026-08-11"
END_DATE = "2026-08-18"

COUNTER_FILE = "counter.json"

def get_and_update_count():
    """قراءة العداد وزيادته بمقدار 1"""
    count = 0
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                data = json.load(f)
                count = data.get("count", 0)
        except Exception:
            count = 0

    count += 1

    try:
        with open(COUNTER_FILE, "w") as f:
            json.dump({"count": count}, f)
    except Exception as e:
        print(f"تعذر حفظ العداد: {e}")

    return count

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"فشل إرسال رسالة تيليجرام: {e}")

def check_availability():
    count = get_and_update_count()
    print(f"رقم عملية الفحص الحالية: {count}")

    # رابط API الخاص بـ SevenRooms
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

        if available_slots:
            msg = f"🚨 **تنبيه توفر مواعيد في Le Café Louis Vuitton!**\n\n"
            msg += f"👥 **عدد الأشخاص:** {PARTY_SIZE}\n\n"
            msg += "\n".join(available_slots)
            msg += f"\n\n🔗 [اضغط هنا للحجز الفوري](https://www.sevenrooms.com/reservations/{VENUE_SLUG})"
            send_telegram(msg)
            print("✅ تم العثور على مواعيد وإرسال التنبيه!")
        else:
            print("ℹ️ لا توجد مواعيد متاحة حالياً.")

            # إرسال إحصائية طمأنة كل 5 مرات فحص
            if count % 5 == 0:
                status_msg = (
                    f"🟢 **تقرير حالة الفحص الدوري**\n\n"
                    f"أنظمة المراقبة تعمل بنجاح! 🤖\n"
                    f"📊 **إجمالي عمليات الفحص:** {count} مرّة\n"
                    f"🎯 **الهدف:** Le Café Louis Vuitton ({START_DATE} إلى {END_DATE})\n\n"
                    f"لاحس ولا خبر حتى الآن، وسيصلك إشعار فور توفر أي حجز! ⏳"
                )
                send_telegram(status_msg)
                print("تم إرسال تقرير الحالة الفصلي إلى تيليجرام.")

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {e}")

if __name__ == "__main__":
    check_availability()
