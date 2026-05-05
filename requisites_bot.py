import logging
import re
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_FILE = "custom_banks.json"

logging.basicConfig(level=logging.INFO)

BANKS = {
    # Сбербанк
    "сбер":             ("🟢", "Сбербанк"),
    "сбербанк":         ("🟢", "Сбербанк"),
    "sber":             ("🟢", "Сбербанк"),
    "sberbank":         ("🟢", "Сбербанк"),
    # Т-Банк
    "т-банк":           ("🟡", "Т-Банк"),
    "тбанк":            ("🟡", "Т-Банк"),
    "t-bank":           ("🟡", "Т-Банк"),
    "tbank":            ("🟡", "Т-Банк"),
    "тинькофф":         ("🟡", "Т-Банк"),
    "tinkoff":          ("🟡", "Т-Банк"),
    # Альфа-Банк
    "альфа":            ("🔴", "Альфа-Банк"),
    "альфабанк":        ("🔴", "Альфа-Банк"),
    "alfa":             ("🔴", "Альфа-Банк"),
    "alpha":            ("🔴", "Альфа-Банк"),
    "alfabank":         ("🔴", "Альфа-Банк"),
    # ВТБ
    "втб":              ("🔵", "ВТБ"),
    "vtb":              ("🔵", "ВТБ"),
    # Райффайзен
    "райфф":            ("🟡", "Райффайзен"),
    "райф":             ("🟡", "Райффайзен"),
    "райффайзен":       ("🟡", "Райффайзен"),
    "raiff":            ("🟡", "Райффайзен"),
    "raiffeisen":       ("🟡", "Райффайзен"),
    # ОТП Банк
    "отп":              ("🟠", "ОТП Банк"),
    "otp":              ("🟠", "ОТП Банк"),
    # Озон Банк
    "озон":             ("🔵", "Озон Банк"),
    "ozon":             ("🔵", "Озон Банк"),
    # Газпромбанк
    "газпром":          ("🔵", "Газпромбанк"),
    "gazprom":          ("🔵", "Газпромбанк"),
    "газпромбанк":      ("🔵", "Газпромбанк"),
    # Яндекс Банк
    "яндекс":           ("🔴", "Яндекс Банк"),
    "yandex":           ("🔴", "Яндекс Банк"),
    # МТС-Банк
    "мтс":              ("🔴", "МТС-Банк"),
    "mts":              ("🔴", "МТС-Банк"),
    "мтсбанк":          ("🔴", "МТС-Банк"),
    # ЮMoney
    "юмани":            ("🟣", "ЮMoney"),
    "юмoney":           ("🟣", "ЮMoney"),
    "yumoney":          ("🟣", "ЮMoney"),
    # Вайлдберис Банк
    "вайлдберис":       ("🟣", "Вайлдберис Банк"),
    "wildberries":      ("🟣", "Вайлдберис Банк"),
    "вб":               ("🟣", "Вайлдберис Банк"),
    "вб банк":          ("🟣", "Вайлдберис Банк"),
    "wb":               ("🟣", "Вайлдберис Банк"),
    # Совкомбанк
    "совком":           ("🟠", "Совкомбанк"),
    "совкомбанк":       ("🟠", "Совкомбанк"),
    "sovkom":           ("🟠", "Совкомбанк"),
    # Уралсиб
    "уралсиб":          ("🔵", "Уралсиб"),
    "uralsib":          ("🔵", "Уралсиб"),
}


def load_custom_banks():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_custom_bank(keyword: str, emoji: str, name: str):
    db = load_custom_banks()
    db[keyword.lower()] = {"emoji": emoji, "name": name}
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def detect_bank(text: str):
    lower = text.lower().replace(" ", "")
    for keyword, (emoji, name) in BANKS.items():
        if keyword in lower:
            return emoji, name
    custom = load_custom_banks()
    for keyword, data in custom.items():
        if keyword in lower:
            return data["emoji"], data["name"]
    return None, None


def parse_all(text: str):
    phone_match = re.search(r'(?<!\d)(\+?[78])[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}(?!\d)', text)
    phone = None
    phone_str = ""
    if phone_match:
        digits = re.sub(r'\D', '', phone_match.group())
        if len(digits) == 11:
            phone = f"+7{digits[1:]}"
            phone_str = phone_match.group()

    card_match = re.search(r'(?<!\d)(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})(?!\d)', text)
    card = None
    card_str = ""
    if card_match:
        card = re.sub(r'[\s\-]', '', card_match.group())
        if len(card) == 16:
            card_str = card_match.group()
        else:
            card = None

    clean = text
    if phone_str:
        clean = clean.replace(phone_str, ' ')
    if card_str:
        clean = clean.replace(card_str, ' ')
    for kw in BANKS:
        clean = re.sub(kw, ' ', clean, flags=re.IGNORECASE)

    amount = None
    currency = "RUB"
    # Support amounts with spaces: "4 000", "10 000", "1 000 000"
    # Support amounts with spaces like '4 000' or '100 000'
    amount_match = re.search(r'(?<!\d)(\d{1,3}(?:[\u0020\u00a0]\d{3})+|\d{2,7})(?!\d)', clean)
    if amount_match:
        amount = int(re.sub(r'[^\d]', '', amount_match.group()))

    cur_match = re.search(r'\b(rub|руб(?:лей|ля)?|₽|usdt|usd|eur)\b', text, re.IGNORECASE)
    if cur_match:
        raw = cur_match.group().upper()
        raw = re.sub(r'РУБ(ЛЕЙ|ЛЯ)?', 'RUB', raw)
        raw = raw.replace('₽', 'RUB')
        currency = raw

    requisite = None
    req_type = None
    if phone:
        requisite = phone
        req_type = "phone"
    elif card:
        requisite = card
        req_type = "card"

    return amount, currency, requisite, req_type


def build_result(amount, currency, requisite, bank_name, bank_emoji) -> str:
    lines = []
    if amount:
        lines.append(f"✅ Сумма: {amount:,} {currency}".replace(",", " "))
    if requisite:
        lines.append(f"💳 Реквизиты: <code>{requisite}</code>")
    lines.append(f"🏦 Банк: {bank_name} {bank_emoji}")
    lines.append("")
    lines.append("⛔ Пожалуйста, будьте внимательны, не ошибитесь банком и суммой ⛔")
    return "\n".join(lines)


def bank_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Сбербанк", callback_data="bank:🟢:Сбербанк"),
         InlineKeyboardButton("🟡 Т-Банк", callback_data="bank:🟡:Т-Банк")],
        [InlineKeyboardButton("🔴 Альфа-Банк", callback_data="bank:🔴:Альфа-Банк"),
         InlineKeyboardButton("🔵 ВТБ", callback_data="bank:🔵:ВТБ")],
        [InlineKeyboardButton("🟡 Райффайзен", callback_data="bank:🟡:Райффайзен"),
         InlineKeyboardButton("🟠 ОТП Банк", callback_data="bank:🟠:ОТП Банк")],
        [InlineKeyboardButton("🔵 Озон Банк", callback_data="bank:🔵:Озон Банк"),
         InlineKeyboardButton("🔵 Газпромбанк", callback_data="bank:🔵:Газпромбанк")],
        [InlineKeyboardButton("🔴 Яндекс Банк", callback_data="bank:🔴:Яндекс Банк"),
         InlineKeyboardButton("🔴 МТС-Банк", callback_data="bank:🔴:МТС-Банк")],
        [InlineKeyboardButton("🟣 ЮMoney", callback_data="bank:🟣:ЮMoney"),
         InlineKeyboardButton("🟣 Вайлдберис Банк", callback_data="bank:🟣:Вайлдберис Банк")],
        [InlineKeyboardButton("🟠 Совкомбанк", callback_data="bank:🟠:Совкомбанк"),
         InlineKeyboardButton("🔵 Уралсиб", callback_data="bank:🔵:Уралсиб")],
        [InlineKeyboardButton("✏️ Другое (ввести вручную)", callback_data="bank:custom")],
    ])


def color_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢", callback_data="color:🟢"),
         InlineKeyboardButton("🔴", callback_data="color:🔴"),
         InlineKeyboardButton("🟡", callback_data="color:🟡"),
         InlineKeyboardButton("🔵", callback_data="color:🔵"),
         InlineKeyboardButton("🟠", callback_data="color:🟠"),
         InlineKeyboardButton("🟣", callback_data="color:🟣"),
         InlineKeyboardButton("⚪", callback_data="color:⚪"),
         InlineKeyboardButton("⚫", callback_data="color:⚫"),
         InlineKeyboardButton("🟤", callback_data="color:🟤")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    custom = load_custom_banks()
    custom_list = ""
    if custom:
        custom_list = "\n\nСохранённые банки:\n" + "\n".join(
            [f"{v['emoji']} {v['name']}" for v in custom.values()]
        )
    await update.message.reply_text(
        "👋 Привет! Я форматирую платёжные реквизиты.\n\n"
        "Просто пришли данные в любом виде:\n"
        "<code>Сбер 11254 2202 3454 1241 2412</code>\n"
        "или\n"
        "<code>Альфа 15000 79161363449</code>" + custom_list,
        parse_mode="HTML"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если ждём название нового банка
    if context.user_data.get("waiting_bank_name"):
        bank_name = update.message.text.strip()
        context.user_data["new_bank_name"] = bank_name
        context.user_data["waiting_bank_name"] = False
        await update.message.reply_text(
            f"Отлично! Теперь выбери цвет кружка для банка <b>{bank_name}</b>:",
            parse_mode="HTML",
            reply_markup=color_keyboard()
        )
        return

    text = update.message.text or ""
    amount, currency, requisite, req_type = parse_all(text)
    bank_emoji, bank_name = detect_bank(text)

    if not amount and not requisite:
        await update.message.reply_text(
            "❌ Не удалось распознать реквизиты.\n\n"
            "Пришли данные в любом формате, например:\n"
            "<code>Сбер 5000 4276 1234 5678 1234</code>\n"
            "или\n"
            "<code>Альфа 15000 79161363449</code>",
            parse_mode="HTML"
        )
        return

    if not bank_name:
        context.user_data["pending_text"] = text
        await update.message.reply_text(
            "🤔 Не удалось определить банк. Выбери из списка:",
            reply_markup=bank_keyboard()
        )
        return

    result = build_result(amount, currency, requisite, bank_name, bank_emoji)
    await update.message.reply_text(result, parse_mode="HTML")


async def handle_bank_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "bank:custom":
        context.user_data["waiting_bank_name"] = True
        await query.edit_message_text("✏️ Напиши название банка:")
        return

    if data.startswith("color:"):
        color = data.split(":", 1)[1]
        bank_name = context.user_data.get("new_bank_name", "Другой банк")
        pending_text = context.user_data.get("pending_text", "")
        keyword = bank_name.lower()
        save_custom_bank(keyword, color, bank_name)
        amount, currency, requisite, _ = parse_all(pending_text)
        result = build_result(amount, currency, requisite, bank_name, color)
        await query.edit_message_text(
            f"✅ Банк <b>{bank_name}</b> {color} сохранён и будет распознаваться автоматически!\n\n" + result,
            parse_mode="HTML"
        )
        context.user_data.clear()
        return

    if data.startswith("bank:"):
        parts = data.split(":", 2)
        bank_emoji = parts[1]
        bank_name = parts[2]
        pending_text = context.user_data.get("pending_text", "")
        amount, currency, requisite, _ = parse_all(pending_text)
        result = build_result(amount, currency, requisite, bank_name, bank_emoji)
        await query.edit_message_text(result, parse_mode="HTML")
        context.user_data.clear()


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_bank_selection))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
