import requests
import urllib3
from telegram import Update, Chat
from telegram.ext import Application, CommandHandler, ContextTypes
from requests.exceptions import RequestException
import threading
import time

# تعطيل تحذيرات SSL بشكل عام
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# قاموس لتخزين الحظر النشط
active_bans = {}

# دالة لتشفير المعرف
async def encrypt_id(user_id):
    try:
        url = f'https://api-ghost.vercel.app/FFcrypto/{user_id}'
        response = requests.get(url, verify=False)  # تعطيل التحقق من SSL
        if response.status_code == 200:
            return response.text.strip()
        else:
            return None
    except RequestException as e:
        print(f"Failed to encrypt ID: {e}")
        return None

# دالة للتحقق مما إذا كانت الرسالة من دردشة خاصة
async def is_private_chat(update: Update):
    if update.message.chat.type == Chat.PRIVATE:
        await update.message.reply_text('لا يمكن استخدام هذا الأمر في المحادثات الخاصة.')
        return True
    return False

# دالة للتعامل مع أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await is_private_chat(update):
        return
    await update.message.reply_text('مرحبًا بك في البوت! استخدم /help لرؤية الأوامر المتاحة.')

# دالة للتعامل مع أمر /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await is_private_chat(update):
        return
    help_text = (
        "الأوامر المتاحة:\n"
        "/start - بدء البوت\n"
        "/add <user_id> <hours> - إضافة معرف المستخدم لساعات محددة\n"
        "/delete <user_id> - حذف المعرف من الخادم\n"
    )
    await update.message.reply_text(help_text)

# دالة للتعامل مع أمر /add
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await is_private_chat(update):
        return
    try:
        args = update.message.text.split()
        user_id = args[1]
        hours = int(args[2])
        encrypted_id = await encrypt_id(user_id)

        if encrypted_id:
            if encrypted_id not in active_bans:
                active_bans[encrypted_id] = hours

                response = requests.post('https://kazawihossam.atwebpages.com/id.php', data={'id': encrypted_id}, verify=False)
                if response.status_code == 200:
                    await update.message.reply_text(f'تم إضافة المعرف {user_id} لمدة {hours} ساعة.')
                    print(f'تم إضافة المعرف {user_id} لمدة {hours} ساعة.')

                    # بدء العداد التنازلي
                    thread = threading.Thread(target=ban_countdown, args=(encrypted_id,))
                    thread.start()
                else:
                    await update.message.reply_text('فشل في إضافة المعرف.')
            else:
                await update.message.reply_text('المعرف موجود بالفعل.')
        else:
            await update.message.reply_text('فشل في تشفير المعرف.')
    except IndexError:
        await update.message.reply_text('استخدام غير صحيح للأمر. التنسيق الصحيح: /add <user_id> <hours>')
    except ValueError:
        await update.message.reply_text('معرف المستخدم أو الساعات المقدمة غير صحيحة.')
    except RequestException:
        await update.message.reply_text('فشل الاتصال بالخادم. حاول مرة أخرى لاحقًا.')
    except Exception as e:
        await update.message.reply_text(f'حدث خطأ غير متوقع: {e}')

# دالة للتعامل مع العداد التنازلي وحذف المعرف
def ban_countdown(encrypted_id):
    try:
        hours = active_bans.get(encrypted_id, 0)
        if hours > 0:
            print(f'بدء العداد التنازلي للمعرف {encrypted_id} لمدة {hours} ساعة.')
            seconds = hours * 3600
            while seconds > 0:
                hrs, secs = divmod(seconds, 3600)
                mins, secs = divmod(secs, 60)
                time_format = f'{hrs:02}:{mins:02}:{secs:02}'
                print(f'العد التنازلي للمعرف {encrypted_id}: {time_format}')
                time.sleep(1)
                seconds -= 1

            print(f'انتهى العداد التنازلي للمعرف {encrypted_id}. يتم الآن حذف المعرف.')

            response = requests.post('https://kazawihossam.atwebpages.com/id.php', data={'id': encrypted_id, 'action': 'delete'}, verify=False)
            if response.status_code == 200:
                print(f'تم حذف المعرف {encrypted_id} بنجاح.')
            else:
                print(f'فشل في حذف المعرف {encrypted_id}.')
            
            # إزالة من الحظر النشط
            del active_bans[encrypted_id]
        else:
            print(f'العد التنازلي للمعرف {encrypted_id} انتهى بالفعل أو لم يتم العثور عليه في الحظر النشط.')

    except RequestException:
        print('فشل الاتصال بالخادم. حاول مرة أخرى لاحقًا.')
    except Exception as e:
        print(f'حدث خطأ غير متوقع أثناء العداد التنازلي: {e}')

# دالة للتعامل مع أمر /delete
async def delete_encrypted_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await is_private_chat(update):
        return
    try:
        user_id = update.message.text.split()[1]
        encrypted_id = await encrypt_id(user_id)
        response = requests.post('https://kazawihossam.atwebpages.com/id.php', data={'id': encrypted_id, 'action': 'delete'}, verify=False)
        if response.status_code == 200:
            await update.message.reply_text(f'تم حذف المعرف {user_id} بنجاح.')
            print(f'تم حذف المعرف {user_id} بنجاح.')

            # إزالة من الحظر النشط إذا كان موجوداً
            if encrypted_id in active_bans:
                del active_bans[encrypted_id]
        else:
            await update.message.reply_text('فشل في حذف المعرف.')
            print(f'فشل في حذف المعرف {user_id}.')
    except IndexError:
        await update.message.reply_text('استخدام غير صحيح للأمر. التنسيق الصحيح: /delete <user_id>')
    except RequestException:
        await update.message.reply_text('فشل الاتصال بالخادم. حاول مرة أخرى لاحقًا.')
    except Exception as e:
        await update.message.reply_text(f'حدث خطأ غير متوقع: {e}')

# الدالة الرئيسية لبدء البوت
def main():
    # استبدل 'YOUR_TOKEN_HERE' بالرمز الفعلي الخاص بك
    application = Application.builder().token("8109629688:AAEWXWt8Z7nY5b__KH-hm2VP5dLxgxt5c6M").build()


    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('add', ban_user))
    application.add_handler(CommandHandler('delete', delete_encrypted_id))

    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()
