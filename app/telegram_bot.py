import logging
import telegram
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackContext,
    ConversationHandler,
    filters,
    ApplicationBuilder,
)

from dotenv import load_dotenv
import os

import gpt_functions


# Logging Configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARNING
)

load_dotenv()
TOKEN = os.getenv("TOKEN")

CHOOSING_VOICE = 0
logging.warning(f"Telegram version: {telegram.__version__}")


async def start(update: Update, context: CallbackContext):
    keyboard = [[KeyboardButton("David"), KeyboardButton("Jane")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Please choose a character:", reply_markup=reply_markup
    )

    # Register a handler for the next message to capture the user's choice
    context.user_data["awaiting_voice_choice"] = True
    return CHOOSING_VOICE


async def handle_voice_choice(update: Update, context: CallbackContext):
    if context.user_data.get("awaiting_voice_choice", False):
        user_choice = update.message.text
        if user_choice in ["David", "Jane"]:
            context.user_data["voice_character"] = user_choice
            await update.message.reply_text(f"Voice character set to {user_choice}.")

            # Unregister the handler after setting the choice
            context.user_data["awaiting_voice_choice"] = False
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "Invalid choice. Please choose 'David' or 'Jane'."
            )


# async def text_response(update: Update, context):
#     message = update.message.text
#     response = gpt_functions.get_gpt_response(message)
#     await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def audio_response(update: Update, context):
    actor = context.user_data.get("voice_character")
    message = update.message.text

    response = gpt_functions.get_gpt_response(message, actor)
    audio = gpt_functions.get_audio_file(response, actor)
    await context.bot.send_voice(
        chat_id=update.effective_chat.id, voice=audio, caption=response
    )


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_VOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_voice_choice)
            ],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, audio_response)
    )  # Replace with your actual command

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
