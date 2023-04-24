import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
import json


with open("config.json") as file:
    data = json.load(file)


# Запускаем логгирование
logging.basicConfig(
    level=logging.INFO
)

bot = Bot(token=data["BOT_TOKEN_1"])
dp = Dispatcher(bot)

# цена 100 руб
PRICE = types.LabeledPrice(label="Приглашение в приватный канал связи", amount=100*100)  # в копейках: 10000


@dp.message_handler(commands=['start']) # При написании команде /start, будут доступны 2 кнопки: /help и /buy
async def start(message: types.Message):
    buttons = [
        [types.KeyboardButton(text="/buy")],
        [types.KeyboardButton(text="/help")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons)
    await message.answer("Привет! Я продаю доступ к приватному чату с ботом.", reply_markup=keyboard)


@dp.message_handler(commands=['help'])
async def helps(message: types.Message):
    button = [
        [types.KeyboardButton(text="/buy")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=button)
    await message.answer("Если хочешь купить доступ к приватному чату с ботом, нажми: /buy.", reply_markup=keyboard)


@dp.message_handler(commands=['buy']) # Отправляет пользывателю счет платежа
async def buy(message: types.Message):
    if data["SBER_TOKEN"].split(':')[1] == 'TEST':
        await bot.send_message(message.chat.id, "Тестовый платеж!!!")

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
                           f" прошел успешно. Ссылка на группу: https://t.me/+14ZHw2YkBSswNzli")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)