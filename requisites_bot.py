import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# ================================
# ВСТАВЬ СВОЙ ТОКЕН СЮДА
BOT_TOKEN = "8630277747:AAF4kFdh1WWWZ_E_S1WxAJTk6YtqJEUErZ8"
# ================================

logging.basicConfig(level=logging.INFO)

# ================================================================
# БАНКИ — добавляй новые сюда в том же формате:
# "ключевое_слово": ("эмодзи", "Название банка"),
# Можно добавить несколько ключевых слов для одного банка.
# ================================================================
BANKS = {
    # Сбербанк 🟢
    "сбер":         ("🟢", "Сбербанк"),
    "sber":         ("🟢", "Сбербанк"),
    "сбербанк":     ("🟢", "Сбербанк"),
    "sberbank":     ("🟢", "Сбербанк"),

    # Альфа-Банк 🔴
    "альфа":        ("🔴", "Альфа-Банк"),
    "alfa":         ("🔴", "Альфа-Банк"),
    "alpha":        ("🔴", "Альфа-Банк"),
    "альфабанк":    ("🔴", "Альфа-Банк"),
    "alfabank":     ("🔴", "Альфа-Банк"),

    # Т-Банк (бывший Тинькофф) 🟡
    "т-банк":       ("🟡", "Т-Банк"),
    "тбанк":        ("🟡", "Т-Банк"),
    "t-bank":       ("🟡", "Т-Банк"),
    "tbank":        ("🟡", "Т-Банк"),
    "тинькофф":     ("🟡", "Т-Банк"),
    "tinkoff":      ("🟡", "Т-Банк"),

    # ================================================================
    # ДОБАВЬ СВОИ БАНКИ НИЖЕ:
    # Пример:
    # "втб":        ("🔵", "ВТБ"),
    # "vtb":        ("🔵", "ВТБ"),
    # "газпром":    ("🔵", "Газпромбанк"),
    # "райфф":      ("🟠", "Райффайзен"),
    # ================================================================
}


def detect_bank(text: str):
    """Определяет банк по ключевым словам в тексте."""
    lower = text.lower().replace(" ", "")
    for keyword, (emoji, name) in BANKS.items():
        if keyword in lower:
            return emoji, name
    return "⚪", "Неизвестный банк"


def extract_amount(text: str):
    """Ищет сумму и валюту в тексте."""
    pattern = r'(\d[\d\s]*)\s*(rub|руб(?:лей|ля)?|₽|usdt|usd|eur)?'
    matches = re.findall(pattern, text, re.IGNORECASE)
    for amount_raw, currency in matches:
        amount = re.sub(r'\s', '', amount_raw)
        if len(amount) >= 2:
            cur = currency.strip().upper() if currency else "RUB"
            cur = re.sub(r'РУБ(ЛЕЙ|ЛЯ)?', 'RUB', cur)
            cur = cur.replace('₽', 'RUB')
            return int(amount), cur
    return None, "RUB"


def extract_requisite(text: str):
    """Извлекает номер карты/счёта или телефон."""
    # Номер карты или счёта (12–20 цифр)
    cards = re.findall(r'\b\d[\d\s\-]{10,22}\d\b', text)
    for c in cards:
        clean = re.sub(r'[\s\-]', '', c)
        if 12 <= len(clean) <= 20:
            return clean, "card"

    # Телефон
    phones = re.findall(r'(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', text)
    if phones:
        digits = re.sub(r'\D', '', phones[0])
        if len(digits) == 11:
            formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
            return formatted, "phone"

    return None, None


def format_requisites(text: str) -> str:
    """Форматирует реквизиты в красивый вид."""
    amount, currency = extract_amount(text)
    requisite, req_type = extract_requisite(text)
    bank_emoji, bank_name = detect_bank(text)

    # Если ничего не нашли — просим уточнить
    if not amount and not requisite:
        return (
            "❌ Не удалось распознать реквизиты.\n\n"
            "Пришли данные в любом формате, например:\n"
            "<code>Сбер, 5000 руб, карта 4276 1234 5678 1234</code>"
        )

    lines = []

    if amount:
        formatted_amount = f"{amount:,}".replace(",", " ")
        lines.append(f"Сумма: {formatted_amount} {currency}")

    if requisite:
        lines.append(f"Реквизиты: <code>{requisite}</code>")

    lines.append(f"Банк: {bank_name} {bank_emoji}")
    lines.append("")
    lines.append("⛔ Пожалуйста, будьте внимательны, не ошибитесь банком ⛔")

    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я форматирую платёжные реквизиты.\n\n"
        "Просто пришли данные в любом виде:\n"
        "<code>Сбер 11254 руб 2202 3454 1241 24</code>\n\n"
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
