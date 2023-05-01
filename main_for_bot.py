import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    BasePersistence,
    PersistenceInput,
    CallbackContext,
    ContextTypes
)
import datetime
import json
from telegram import ReplyKeyboardMarkup, Update
from weather_API import Weather
import sqlite3
import typing as t
from collections import defaultdict
from telegram.ext._utils.types import UD, CD


class SqlitePersistence(BasePersistence): # сохраняет все сообщения в БД
    def __init__(self, name: str = 'date.db'):
        # update_interval - это время, как часто состояние chat_data будут сохраняться в хранилище
        super().__init__(update_interval=1) # 1 сек

        # store_data определяет какие данные будут храниться
        self.store_data = PersistenceInput(chat_data=True, bot_data=False, user_data=False, callback_data=False)

        # подключение к базе данных
        self.conn = sqlite3.connect(name)
        self.cursor = self.conn.cursor()

    async def get_chat_data(self) -> t.DefaultDict[int, t.Any]:
        # получаем данные для всех чатов
        data = self.cursor.execute('''SELECT * FROM chat_data''').fetchall()
        chat_data = defaultdict(dict)

        # проходим по всем строчкам из таблицы и заполняем словарь chat_data
        # Чтобы к каждому chat_id относились только свои сообщения
        for row in data:
            chat_id = row[1]
            if 'messages' not in chat_data[chat_id]:
                chat_data[chat_id] = {'messages': []}
            chat_data[chat_id]['messages'].append(dict(zip(['id', 'chat_id', 'message_ts', 'message'], row)))
        return chat_data
    # Обновляет или добавляет сообщение
    async def update_chat_data(self, chat_id: int, data: CD) -> None:
        for row in data['messages']:
            db_row = self.cursor.execute('''SELECT * 
                                            FROM chat_data 
                                            WHERE chat_id = ? AND message_ts = ? AND message = ?''',
                                         (chat_id, row['message_ts'], row['message'])).fetchone()
            if db_row is None: # Если такого сообщения нет, то его добавляют
                self.cursor.execute('''INSERT INTO chat_data
                                           (chat_id, message_ts, message)
                                       VALUES 
                                           (?, ?, ?)''', (chat_id, row['message_ts'], row['message']))
            else: # иначе обновляет
                self.cursor.execute('''UPDATE chat_data
                SET
                    message = ?
                WHERE
                    chat_id = ? AND message_ts = ?
                ''', (row['message'], chat_id, row['message_ts']))
        self.conn.commit()
    # Из бд обновляет данные в памяти
    async def refresh_chat_data(self, chat_id: int, chat_data: t.Any) -> None:
        data = self.cursor.execute('''SELECT * FROM chat_data WHERE chat_id = ?''', (chat_id,))
        chat_data['messages'] = [dict(zip(['id', 'chat_id', 'message_ts', 'message'], x)) for x in data]
    # просто удаляет
    async def drop_chat_data(self, chat_id: int) -> None:
        self.cursor.execute('''DELETE * FROM chat_data WHERE chat_id = ?''', (chat_id,))
    # все остальные должны быть со значением pass, иначе будут происходить непонятные ошибки
    async def get_bot_data(self) -> t.Any:
        pass

    def update_bot_data(self, data) -> None:
        pass

    def refresh_bot_data(self, bot_data) -> None:
        pass

    def get_user_data(self) -> t.DefaultDict[int, t.Any]:
        pass

    def update_user_data(self, user_id: int, data: t.Any) -> None:
        pass

    def refresh_user_data(self, user_id: int, user_data: t.Any) -> None:
        pass

    def get_callback_data(self) -> t.Optional[t.Any]:
        pass

    def update_callback_data(self, data: t.Any) -> None:
        pass

    def get_conversations(self, name: str) -> t.Any:
        pass

    def update_conversation(self, name: str, key, new_state: t.Optional[object]) -> None:
        pass

    def flush(self) -> None:
        self.conn.close()

    async def drop_user_data(self, user_id: int) -> None:
        pass

    async def get_user_data(self) -> t.Dict[int, UD]:
        pass


# Кнопки
reply_keyboard = [['/help', '/date', '/show_data'],
                  ['/time', '/weather']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
# Словарь, который будет из запроса пользывателя возращать ответ по погоде
dct = {}

with open("config.json") as file: # файл с токенами
    data = json.load(file)

# Запускаем логгирование и сохроняем все в bot.log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG, filename='bot.log'
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
    await update.message.reply_text("Привет! Я - бот Энгри. У меня есть куча полезных функций, например: \n"
                                    "- Влажность воздуха \n"
                                    "- Температура \n"
                                    "- Все сообщения, за все время \n"
                                    "- и т.д. Эксперементируй!")


async def time_now(update, context):
    await update.message.reply_text(f"Время: {datetime.datetime.now().strftime('%X')}")


async def date_today(update, context):
    await update.message.reply_text(f"Дата: {datetime.datetime.now().date()}")


async def weather(update, context):
    await update.message.reply_text(f"О каком городе найти информацию? Напишите на английском.")
    return 1


async def first_response(update, context):
    global dct
    flag = True
    keyboards = [['Температура', 'Давление'],
                 ['Влажность', 'Все вместе']]
    markup_2 = ReplyKeyboardMarkup(keyboards, one_time_keyboard=False)

    try:
        w = Weather(update.message.text)

        dct = {'Температура': w.temp(),
               'Давление': w.pressure(),
               'Влажность': w.humidity(),
               'Все вместе': w.all()}

    except Exception as ex:
        await update.message.reply_text("Что?",
                                        reply_markup=markup
                                        )
        flag = False

    if flag:
        await update.message.reply_text(
            "Что вы хотите узнать?",
            reply_markup=markup_2
            )
        return 2


async def second_response(update, context):
    information = dct[update.message.text]
    await update.message.reply_text(information,
                                    reply_markup=markup)
    return ConversationHandler.END


async def stop(update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"Всего доброго!, {user.mention_html()}")
    return ConversationHandler.END


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def _read_messages(chat_messages):
        return '\n'.join([f'{x["message_ts"]}: {x["message"]}' for x in chat_messages])

    messages = [f"\n{key}:\n{_read_messages(value)}" for key, value in context.chat_data.items()]
    facts = '\n'.join(messages)
    await update.message.reply_text(
        f"Все сообщения: {facts}"
    )

# Сохроняет все сообщения
async def save_message(update: Update, context: CallbackContext) -> None:
    if 'messages' not in context.chat_data:
        context.chat_data['messages'] = []
    context.chat_data['messages'].append({'message': update.message.text,
                                          'message_ts': update.message.date.timestamp()}) # (4)


def main() -> None:
    persistence = SqlitePersistence()
    application = Application.builder().token(data["BOT_TOKEN_2"]).persistence(persistence).build()

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
    application.add_handler(CommandHandler("weather", weather))
    application.add_handler(CommandHandler("show_data", show_data))
    try:
        application.add_handler(MessageHandler(filters=filters.ALL, callback=save_message))  # (3)
        application.run_polling()
    except Exception:
        print()


if __name__ == '__main__':
    main()