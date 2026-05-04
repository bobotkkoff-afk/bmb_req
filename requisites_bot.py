import logging
import re
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

BANKS = {
    "сбер":         ("🟢", "Сбербанк"),
    "sber":         ("🟢", "Сбербанк"),
    "сбербанк":     ("🟢", "Сбербанк"),
    "sberbank":     ("🟢", "Сбербанк"),
    "альфа":        ("🔴", "Альфа-Банк"),
    "alfa":         ("🔴", "Альфа-Банк"),
    "alpha":        ("🔴", "Альфа-Банк"),
    "альфабанк":    ("🔴", "Альфа-Банк"),
    "alfabank":     ("🔴", "Альфа-Банк"),
    "т-банк":       ("🟡", "Т-Банк"),
    "тбанк":        ("🟡", "Т-Банк"),
    "t-bank":       ("🟡", "Т-Банк"),
    "tbank":        ("🟡", "Т-Банк"),
    "тинькофф":     ("🟡", "Т-Банк"),
    "tinkoff":      ("🟡", "Т-Банк"),
    # ДОБАВЬ СВОИ БАНКИ НИЖЕ:
    # "втб":        ("🔵", "ВТБ"),
    # "газпром":    ("🔵", "Газпромбанк"),
}


def detect_bank(text: str):
    lower = text.lower().replace(" ", "")
    for keyword, (emoji, name) in BANKS.items():
        if keyword in lower:
            return emoji, name
    return "⚪", "Неизвестный банк"


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
    amount_match = re.search(r'(?<!\d)(\d{2,7})(?!\d)', clean)
    if amount_match:
        amount = int(amount_match.group())

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


def format_requisites(text: str) -> str:
    amount, currency, requisite, req_type = parse_all(text)
    bank_emoji, bank_name = detect_bank(text)

    if not amount and not requisite:
        return (
            "❌ Не удалось распознать реквизиты.\n\n"
            "Пришли данные в любом формате, например:\n"
            "<code>Сбер 5000 4276 1234 5678 1234</code>\n"
            "или\n"
            "<code>Альфа 15000 79161363449</code>"
        )

    lines = []
    if amount:
        lines.append(f"✅ Сумма: {amount:,} {currency}".replace(",", " "))
    if requisite:
        lines.append(f"💳 Реквизиты: <code>{requisite}</code>")
    lines.append(f"🏛️ Банк: {bank_name} {bank_emoji}")
    lines.append("")
    lines.append("🔔 Пожалуйста, будьте внимательны, не ошибитесь банком 🔔")

    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я форматирую платёжные реквизиты.\n\n"
        "Просто пришли данные в любом виде:\n"
        "<code>Сбер 11254 2202 3454 1241 2412</code>\n"
        "или\n"
        "<code>Альфа 15000 79161363449</code>\n\n"
        "Поддерживаемые банки:\n"
        "🟢 Сбербанк\n"
        "🔴 Альфа-Банк\n"
        "🟡 Т-Банк (Тинькофф)",
        parse_mode="HTML"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    result = format_requisites(text)
    await update.message.reply_text(result, parse_mode="HTML")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
