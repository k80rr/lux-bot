from telegram import Update, ChatPermissions, ChatAdministratorRights
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode

TOKEN = "8990345547:AAGwkM5ognSz1--Gf7Om8uYXmE3Bm-Jx2LQ"

group_settings = {}
warnings_data = {}  # لتخزين التحذيرات {chat_id: {user_id: count}}
last_messages = {}  # لمنع التكرار {chat_id: {user_id: last_text}}

async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    elif context.args:
        try:
            user_id = int(context.args[0])
            member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            return member.user
        except Exception:
            return None
    return None

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in ['administrator', 'creator']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أنا بوت لوكس لإدارة وحماية الكروبات 🛡️🤖\nاكتب (لوكس لستة) لعرض كافة الأوامر العربية.")

# قائمة الأوامر الشاملة بالعربي بالكامل
async def show_full_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_list_text = (
        "🤖 **قائمة أوامر وخصائص بوت لوكس (بالعربي بالكامل):**\n\n"
        "💬 **الردود التلقائية والترحيب:**\n"
        "- اكتب **(لوكس)** ➔ يرد: `هلا 🌸`\n"
        "- اكتب **(السلام عليكم)** ➔ يرد: `وعليكم السلام ورحمة الله وبركاته 🌸`\n"
        "- اكتب **(صباح الخير)** ➔ يرد: `صباح النور والسرور ✨`\n"
        "- الترحيب بالأعضاء الجدد تلقائياً.\n\n"
        "👑 **نظام إدارة المشرفين (بالرد على الرسالة):**\n"
        "- **رفع مشرف** : لرفع العضو مشرفاً.\n"
        "- **تنزيل مشرف** : لسحب الإشراف.\n\n"
        "⚡ **أوامر الإدارة والتحكم (بالرد على الرسالة):**\n"
        "- **طرد** : لطرد العضو.\n"
        "- **حظر** : لحظر العضو نهائياً.\n"
        "- **تحذير** : إنذار العضو (3 تحذيرات = حظر تلقائي).\n"
        "- **كتم** : لكتم العضو.\n"
        "- **إلغاء كتم** : لإلغاء الكتم.\n"
        "- **تثبيت** : لتثبيت رسالة مهمة.\n"
        "- **حذف** : لحذف رسالة.\n"
        "- **حذف [العدد]** : لحذف عدة رسائل (مثال: حذف 10).\n"
        "- **إحصائيات** : إحصائيات المجموعة.\n"
        "- **آيدي** : معرفة الآيدي والمعرف.\n\n"
        "🛡️ **أوامر الحماية والتفعيل:**\n"
        "- **قفل الروابط** / **فتح الروابط**\n"
        "- **قفل الصور** / **فتح الصور**\n"
        "- **منع التكرار** / **السماح بالتكرار**\n"
        "- **تفعيل الترحيب** / **تعطيل الترحيب**\n"
    )
    await update.message.reply_text(full_list_text, parse_mode=ParseMode.MARKDOWN)

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    target = await get_target_user(update, context) or update.effective_user
    username = f"@{target.username}" if target.username else "لا يوجد معرف"
    await update.message.reply_text(
        f"🆔 **معلومات الآيدي:**\n👤 آيدي العضو: <code>{target.id}</code>\n🌐 المعرف: {username}\n📌 آيدي المجموعة: <code>{chat.id}</code>", 
        parse_mode=ParseMode.HTML
    )

async def promote_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("يرجى الرد على رسالة العضو لرفعه مشرفاً.")
    try:
        rights = ChatAdministratorRights(
            is_anonymous=False, can_manage_chat=True, can_delete_messages=True,
            can_restrict_members=True, can_invite_users=True, can_pin_messages=True
        )
        await context.bot.promote_chat_member(update.effective_chat.id, target.id, administrator_rights=rights)
        await update.message.reply_text(f"تم ترقية العضو {target.mention_html()} إلى مشرف بنجاح 👑", parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text("تعذر رفع العضو مشرفاً، تأكد من صلاحيات البوت.")

async def demote_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("يرجى الرد على رسالة المشرف لتنزيله.")
    try:
        rights = ChatAdministratorRights(
            is_anonymous=False, can_manage_chat=False, can_delete_messages=False,
            can_restrict_members=False, can_invite_users=False, can_pin_messages=False
        )
        await context.bot.promote_chat_member(update.effective_chat.id, target.id, administrator_rights=rights)
        await update.message.reply_text(f"تم تنزيل المشرف {target.mention_html()} وإزالة صلاحياته 🔻", parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text("تعذر سحب الصلاحيات.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("يرجى الرد على رسالة العضو لحظره.")
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"تم حظر العضو {target.mention_html()} بنجاح 🚫", parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text("تعذر حظر العضو.")

async def kick_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("يرجى الرد على رسالة العضو لطرده.")
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"تم طرد العضو {target.mention_html()} بنجاح 👢", parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text("تعذر طرد العضو.")

async def warn_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("يرجى الرد على رسالة العضو لتحذيره.")
    
    chat_id = update.effective_chat.id
    user_id = target.id
    
    if chat_id not in warnings_data:
        warnings_data[chat_id] = {}
    
    warnings_data[chat_id][user_id] = warnings_data[chat_id].get(user_id, 0) + 1
    current_warns = warnings_data[chat_id][user_id]
    
    if current_warns >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            warnings_data[chat_id][user_id] = 0
            await update.message.reply_text(f"وصل العضو {target.mention_html()} إلى 3 تحذيرات وتم حظره تلقائياً! 🚫", parse_mode=ParseMode.HTML)
        except Exception:
            await update.message.reply_text("تعذر حظر العضو بعد التحذيرات.")
    else:
        await update.message.reply_text(f"تم تحذير العضو {target.mention_html()} ({current_warns}/3) ⚠️", parse_mode=ParseMode.HTML)

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("يرجى الرد على رسالة العضو لكتمه.")
    try:
        permissions = ChatPermissions(can_send_messages=False)
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=permissions)
        await update.message.reply_text(f"تم كتم العضو {target.mention_html()} 🔇", parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text("تعذر كتم العضو.")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("يرجى الرد على رسالة العضو لإلغاء كتمه.")
    try:
        permissions = ChatPermissions(
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True
        )
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=permissions)
        await update.message.reply_text(f"تم إلغاء كتم العضو {target.mention_html()} 🔊", parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text("تعذر إلغاء الكتم.")

async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("يرجى الرد على الرسالة المراد تثبيتها.")
    try:
        await context.bot.pin_chat_message(update.effective_chat.id, update.message.reply_to_message.message_id)
        await update.message.reply_text("تم تثبيت الرسالة بنجاح 📌")
    except Exception:
        await update.message.reply_text("تعذر تثبيت الرسالة.")

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("يرجى الرد على الرسالة المراد حذفها.")
    try:
        await update.message.reply_to_message.delete()
        await update.message.delete()
    except Exception:
        await update.message.reply_text("تعذر حذف الرسالة.")

async def group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذا الأمر للمشرفين فقط!")
    chat = update.effective_chat
    try:
        count = await chat.get_member_count()
        await update.message.reply_text(
            f"📊 **إحصائيات المجموعة:**\n📌 اسم المجموعة: {chat.title}\n👥 عدد الأعضاء: {count}\n🆔 آيدي المجموعة: <code>{chat.id}</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await update.message.reply_text("تعذر جلب الإحصائيات.")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        chat_id = update.effective_chat.id
        is_welcomed = group_settings.get(chat_id, {}).get("welcome", True)
        if is_welcomed:
            custom_msg = f"أهلاً بك يا {member.mention_html()} في الكروب! منورنا 🌸"
            await update.message.reply_text(custom_msg, parse_mode=ParseMode.HTML)

async def manage_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("عذراً، هذه الأوامر للمشرفين فقط!")
    
    chat_id = update.effective_chat.id
    command = update.message.text.lower()
    
    if chat_id not in group_settings:
        group_settings[chat_id] = {"links": False, "photos": False, "spam": False, "welcome": True}
        
    if "قفل الروابط" in command:
        group_settings[chat_id]["links"] = True
        await update.message.reply_text("تم قفل الروابط بنجاح 🔒🚫")
    elif "فتح الروابط" in command:
        group_settings[chat_id]["links"] = False
        await update.message.reply_text("تم فتح الروابط 🔓✅")
    elif "قفل الصور" in command:
        group_settings[chat_id]["photos"] = True
        await update.message.reply_text("تم قفل الصور بنجاح 🔒🖼️")
    elif "فتح الصور" in command:
        group_settings[chat_id]["photos"] = False
        await update.message.reply_text("تم فتح الصور 🔓🖼️")
    elif "منع التكرار" in command:
        group_settings[chat_id]["spam"] = True
        await update.message.reply_text("تم تفعيل منع التكرار بنجاح 🛡️")
    elif "السماح بالتكرار" in command:
        group_settings[chat_id]["spam"] = False
        await update.message.reply_text("تم إيقاف منع التكرار 🔓")
    elif "تفعيل الترحيب" in command:
        group_settings[chat_id]["welcome"] = True
        await update.message.reply_text("تم تفعيل الترحيب بالأعضاء الجدد بنجاح ✨")
    elif "تعطيل الترحيب" in command:
        group_settings[chat_id]["welcome"] = False
        await update.message.reply_text("تم تعطيل الترحيب 🔕")

async def monitor_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_chat:
        return
    
    text = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in group_settings:
        group_settings[chat_id] = {"links": False, "photos": False, "spam": False, "welcome": True}

    if text:
        clean_text = text.strip()
        
        if clean_text == "لوكس لستة":
            await show_full_list(update, context)
            return
        elif "لوكس" in clean_text:
            await update.message.reply_text("هلا 🌸")
            return
        elif "السلام عليكم" in clean_text:
            await update.message.reply_text("وعليكم السلام ورحمة الله وبركاته 🌸")
            return
        elif "صباح الخير" in clean_text:
            await update.message.reply_text("صباح النور والسرور ✨")
            return
        
        # الأوامر العربية الكاملة بالرد على الرسالة
        if update.message.reply_to_message:
            if clean_text == "رفع مشرف":
                await promote_member(update, context)
                return
            elif clean_text == "تنزيل مشرف":
                await demote_member(update, context)
                return
            elif clean_text == "حظر":
                await ban(update, context)
                return
            elif clean_text == "طرد":
                await kick_member(update, context)
                return
            elif clean_text == "تحذير":
                await warn_member(update, context)
                return
            elif clean_text == "كتم":
                await mute(update, context)
                return
            elif clean_text == "إلغاء كتم":
                await unmute(update, context)
                return
            elif clean_text == "تثبيت":
                await pin_message(update, context)
                return
            elif clean_text == "حذف":
                await delete_message(update, context)
                return

        # الأوامر المفردة (بدون رد أو بطلب عام)
        if clean_text == "إحصائيات" and await is_admin(update, context):
            await group_stats(update, context)
            return
        elif clean_text == "آيدي":
            await id_cmd(update, context)
            return

        # أمر الحذف الجماعي مثل "حذف 10"
        if clean_text.startswith("حذف ") and await is_admin(update, context):
            try:
                count = int(clean_text.split()[1])
                current_id = update.message.message_id
                for i in range(count + 1):
                    try:
                        await context.bot.delete_message(chat_id, current_id - i)
                    except Exception:
                        pass
                return
            except Exception:
                pass

    if await is_admin(update, context):
        return

    # منع التكرار
    if group_settings[chat_id].get("spam", False) and text:
        if chat_id not in last_messages:
            last_messages[chat_id] = {}
        if last_messages[chat_id].get(user_id) == text:
            try:
                await update.message.delete()
                return
            except Exception:
                pass
        last_messages[chat_id][user_id] = text

    # حماية الروابط
    if group_settings[chat_id].get("links", False) and text:
        if "http://" in text or "https://" in text or "t.me/" in text:
            try:
                await update.message.delete()
                await update.message.reply_text(f"عذراً {update.effective_user.mention_html()}, الروابط ممنوعة هنا! 🚫", parse_mode=ParseMode.HTML)
                return
            except Exception:
                pass

    # حماية الصور
    if group_settings[chat_id].get("photos", False) and update.message.photo:
        try:
            await update.message.delete()
            await update.message.reply_text(f"عذراً {update.effective_user.mention_html()}, الصور ممنوعة هنا! 🚫", parse_mode=ParseMode.HTML)
            return
        except Exception:
            pass

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    
    # معالجة كافة الرسائل والأوامر بالعربي بالكامل عبر monitor_messages
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(قفل|فتح|منع|السماح|تفعيل|تعطيل)'), manage_settings))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.ALL, monitor_messages))

    print("بوت لوكس العربي الخارق يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
