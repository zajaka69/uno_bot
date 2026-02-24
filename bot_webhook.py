import os
import json
import logging
import requests
from flask import Flask, request

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
PORT = int(os.environ.get('PORT', 10000))

# Ссылки на документы
PEDAGOGICAL_LINK = "https://docs.google.com/spreadsheets/d/1v4xlteVMrNZJ4vp2x3T_FxEFwC_4yUX2/edit?gid=1331177780#gid=1331177780"
EDUCATIONAL_LINK = "https://disk.360.yandex.net/your-working-link"  # ЗАМЕНИТЕ!

# URL для отправки ответов
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Flask приложение
flask_app = Flask(__name__)

def send_message(chat_id, text, keyboard=None):
    """Отправка сообщения через Telegram API"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if keyboard:
        payload['reply_markup'] = json.dumps(keyboard)
    
    try:
        response = requests.post(url, json=payload)
        logger.info(f"Отправлено сообщение: {response.status_code}")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")

def create_keyboard():
    """Создание клавиатуры с кнопками-ссылками"""
    return {
        'inline_keyboard': [
            [{'text': '📚 Педагогическая работа', 'url': PEDAGOGICAL_LINK}],
            [{'text': '👥 Воспитательная работа', 'url': EDUCATIONAL_LINK}],
            [{'text': '❓ Помощь', 'callback_data': 'help'}]
        ]
    }

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка сообщений от Telegram"""
    try:
        update = request.get_json()
        logger.info(f"Получено обновление: {update.get('update_id')}")
        
        # Обработка команды /start
        if 'message' in update and 'text' in update['message']:
            chat_id = update['message']['chat']['id']
            text = update['message']['text']
            
            if text == '/start':
                keyboard = create_keyboard()
                send_message(
                    chat_id, 
                    "Здравствуйте! Я бот-помощник. Выберите нужный раздел:",
                    keyboard
                )
        
        # Обработка callback-запросов (нажатия на кнопки)
        elif 'callback_query' in update:
            query = update['callback_query']
            chat_id = query['message']['chat']['id']
            callback_data = query['data']
            
            if callback_data == 'help':
                help_text = (
                    "📋 <b>Как пользоваться ботом:</b>\n\n"
                    "• Нажмите на кнопку с названием раздела\n"
                    "• Ссылка откроется в браузере автоматически\n\n"
                    "❓ По вопросам доступа обращайтесь к администратору"
                )
                send_message(chat_id, help_text)
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return 'Error', 500

@flask_app.route('/health')
def health():
    return 'OK', 200

@flask_app.route('/')
def index():
    return 'Бот для педагогических документов работает!'

@flask_app.route('/setup-webhook')
def setup_webhook():
    """Установка webhook (вызвать один раз)"""
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    url = f"{TELEGRAM_API_URL}/setWebhook"
    response = requests.post(url, json={'url': webhook_url})
    return response.json()

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=PORT)
