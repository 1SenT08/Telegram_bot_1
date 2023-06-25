import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
import json


with open("config.json") as file:
    data = json.load(file)


# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG, filename='bot_2.log'
)

bot = Bot(token=data["BOT_TOKEN_1"])
dp = Dispatcher(bot)

# цена за доступ 100 руб
PRICE = types.LabeledPrice(label="Приглашение в приватный канал связи", amount=100*100)  # в копейках: 10000


@dp.message_handler(commands=['start']) # При написании команде /start, будут доступны 2 кнопки: /help и /buy
async def start(message: types.Message):
    buttons = [
        [types.KeyboardButton(text="Купить подписку")],
        [types.KeyboardButton(text="Помощь")],
        [types.KeyboardButton(text="Реквизиты")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons)
    await message.answer("Привет! Я-  бот продавец. С моей помощью, ты можешь купить доступ к боту - Энгри! "
                         "У Энгри есть множество интересных функций, а также у него ты можешь пройти викторину!"
                         " Так что спеши приобрести платный доступ!",
                         reply_markup=keyboard)


@dp.message_handler(text="Помощь")
async def helps(message: types.Message):
    buttons = [
        [types.KeyboardButton(text="Купить подписку")],
        [types.KeyboardButton(text="Помощь")],
        [types.KeyboardButton(text="Реквизиты")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons)
    await message.answer("Если хочешь купить доступ к приватному чату с ботом, нажми на кнопку - Купить подписку. \n"
                         "Если хочешь получить бесплатные реквизиты, нажми на Реквизиты", reply_markup=keyboard)

# Бот отправит тестовые реквизиты
@dp.message_handler(text="Реквизиты") # Отправляет пользывателю счет платежа
async def requisites(message: types.Message):
    await bot.send_message(message.chat.id, "Тестовые реквизиты: \n"
                                            " Номер карты: 4111 1111 1111 1111 \n"
                                            " Дата истечения срока действия: 2024/12 \n"
                                            " Проверочный код на обратной стороне: 123 \n"
                                            " Проверочный код 3-D Secure: 12345678 \n")


@dp.message_handler(text='Купить подписку') # Отправляет пользывателю счет платежа
async def buy(message: types.Message):
    if data["SBER_TOKEN"].split(':')[1] == 'TEST':
        await bot.send_message(message.chat.id, "Тестовый платеж!!!"
                                                " Для получения тестовых реквизитов, напишите: /requisites")

    await bot.send_invoice(message.chat.id,
                           title="Приватный канал с ботом",
                           description="Приглашение в приватный канал связи",
                           provider_token=data["SBER_TOKEN"],
                           currency="rub",
                           photo_url="https://add-groups.com/uploads/posts/old/211/19396_original.jpg",
                           photo_width=416,
                           photo_height=234,
                           photo_size=416,
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter="one-month-subscription",
                           payload="test-invoice-payload")

# Обработка и утверждение платежа, есть только 10 сек, иначе платеж будет откланен(авто)
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# Обработка успешно проведенного платежа
@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    for i, j in payment_info.items():
        print(f"{i} = {j}")

    await bot.send_message(message.chat.id,
                           f"Платёж на сумму {message.successful_payment.total_amount // 100}"
                           f" {message.successful_payment.currency}"
                           f" прошел успешно. Ссылка на приватного бота: t.me/First_test_108_bot")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)