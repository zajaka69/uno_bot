import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------- НАСТРОЙКИ ----------
BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
PORT = int(os.environ.get('PORT', 10000))

# Ваши ссылки на документы (ЗАМЕНИТЕ НА РАБОЧИЕ!)
PEDAGOGICAL_LINK = "https://docs.google.com/spreadsheets/d/1v4xlteVMrNZJ4vp2x3T_FxEFwC_4yUX2/edit?gid=1331177780#gid=1331177780"
EDUCATIONAL_LINK = "https://disk.360.yandex.net/your-working-link"  # ВСТАВЬТЕ ПУБЛИЧНУЮ ССЫЛКУ

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# --------------------------------

# Создаем Flask приложение
flask_app = Flask(__name__)

# Глобальная переменная для приложения бота
bot_application = None

# ---------- ОБРАБОТЧИКИ КОМАНД ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Педагогическая работа", url=PEDAGOGICAL_LINK)],
        [InlineKeyboardButton("👥 Воспитательная работа", url=EDUCATIONAL_LINK)],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Здравствуйте! Я бот-помощник. Выберите нужный раздел:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'help':
        help_text = (
            "📋 **Как пользоваться ботом:**\n\n"
            "• Нажмите на кнопку с названием раздела\n"
            "• Ссылка откроется в браузере автоматически\n\n"
            "❓ По вопросам доступа обращайтесь к администратору"
        )
        await query.edit_message_text(text=help_text)
# ------------------------------------------

# ---------- ИНИЦИАЛИЗАЦИЯ БОТА ----------
async def init_bot():
    """Создание и инициализация приложения бота"""
    global bot_application
    
    # Создаем приложение без Updater (для webhook)
    bot_application = (
        Application.builder()
        .token(BOT_TOKEN)
        .updater(None)  # Явно отключаем Updater для webhook режима
        .build()
    )
    
    # Добавляем обработчики
    bot_application.add_handler(CommandHandler("start", start))
    bot_application.add_handler(CallbackQueryHandler(button_handler))
    
    # Инициализируем
    await bot_application.initialize()
    await bot_application.start()
    
    # Устанавливаем webhook
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        await bot_application.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook установлен на {webhook_url}")
    
    return bot_application
# ------------------------------------------

# ---------- WEBHOOK ----------
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Точка входа для сообщений от Telegram"""
    try:
        update_data = request.get_json(force=True)
        logger.info(f"Получено обновление: {update_data.get('update_id')}")
        
        update = Update.de_json(update_data, bot_application.bot)
        
        # Обрабатываем обновление
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot_application.process_update(update))
        loop.close()
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        return 'Error', 500

@flask_app.route('/health')
def health():
    return 'OK', 200

@flask_app.route('/')
def index():
    return 'Бот для педагогических документов работает!'
# ------------------------------

# ---------- ТОЧКА ВХОДА ----------
if __name__ == '__main__':
    # Инициализируем бота в отдельном цикле событий
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_bot())
    
    # Запускаем Flask
    flask_app.run(host='0.0.0.0', port=PORT)
