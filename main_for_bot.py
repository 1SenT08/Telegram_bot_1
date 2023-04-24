import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import datetime
import json
from telegram import ReplyKeyboardMarkup
from weather_API import Weather


reply_keyboard = [['/help', '/date'],
                  ['/time', '/weather']]

keyboards = [['Темпиратура', 'Давление'],
            ['Влажность', 'Все вместе']]
dct = {}


markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
markup_2 = ReplyKeyboardMarkup(keyboards, one_time_keyboard=False)

with open("config.json") as file:
    data = json.load(file)

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}!",
        reply_markup=markup
    )


async def help_command(update, context):
    """Отправляет сообщение когда получена команда /help"""
    await update.message.reply_text("Я пока не умею помогать... Я только ваше эхо.")


async def time_now(update, context):
    await update.message.reply_text(f"Время: {datetime.datetime.now().strftime('%X')}")


async def date_today(update, context):
    await update.message.reply_text(f"Дата: {datetime.datetime.now().date()}")


async def weather(update, context):
    await update.message.reply_text("О каком городе найти информацию? Напишите на английском.")
    return 1


async def first_response(update, context):
    global dct
    city = update.message.text
    w = Weather(city)
    dct = {'Темпиратура': w.temp(),
           'Давление': w.pressure(),
           'Влажность': w.humidity(),
           'Все вместе': w.all()}
    await update.message.reply_text(
        "Что вы хотите узнать?",
        reply_markup=markup_2
        )
    return 2


async def second_response(update, context):
    information = dct['update.message.text']
    await update.message.reply_text(information)
    return ConversationHandler.END


async def stop(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


def main():
    application = Application.builder().token(data["BOT_TOKEN_2"]).build()

    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /weather. Она задаёт первый вопрос.
        entry_points=[CommandHandler('weather', weather)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
            # Функция читает ответ на второй вопрос и завершает диалог.
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("time", time_now))
    application.add_handler(CommandHandler("date", date_today))
    application.run_polling()


if __name__ == '__main__':
    main()