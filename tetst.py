import logging
from typing import Dict
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PicklePersistence,
    filters,
    CallbackContext
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Demo pickle persistence')


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the gathered info."""
    def _read_messages(chat_messages):
        return '\n'.join([f'{x["message_ts"]}: {x["message"]}' for x in chat_messages])

    messages = [f"\n{key}:\n{_read_messages(value)}" for key, value in context.chat_data.items()]
    facts = '\n'.join(messages)
    await update.message.reply_text(
        f"This is what you already told me: {facts}"
    )


async def save_message(update: Update, context: CallbackContext) -> None:
    if 'messages' not in context.chat_data:
        context.chat_data['messages'] = []
    context.chat_data['messages'].append({'message': update.message.text, 'message_ts': update.message.date.timestamp()}) # (4)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath='persitencebot', update_interval=1) # (1)
    application = Application.builder().token('6043220126:AAGxvii_DmE_L6BJMal0ruLXVBQZFrNQ9u0').persistence(persistence).build() # (2)
    show_data_handler = CommandHandler("show_data", show_data)
    application.add_handler(show_data_handler)
    application.add_handler(MessageHandler(filters=filters.ALL, callback=save_message)) # (3)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()