from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from dotenv import dotenv_values

config = dotenv_values(".env")
API_key = config['BOT_API']

async def day(update: Update, context: ContextTypes):
    wallet_addy = (update.message.text.split(" ")[1:][0]).split(",")

    await update.message.reply_text('tttt')


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(API_key).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("day", day))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
   
main()