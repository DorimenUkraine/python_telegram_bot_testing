#!/usr/bin/python3+
from datetime import time
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, KeyboardButton, ParseMode)
from telegram.ext.dispatcher import run_async

import os
from dotenv import load_dotenv
load_dotenv

############################### GLOBAL SETTINGS ############################################

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TOKEN')
START_WORKING_DAY = time(10, 19, 00, 000000, tzinfo=None)  # -3 по Киеву


############################### GENERAL STARTING COMMAND ############################################
def get_description():
    return """/help - Помощь
/start - Запуск бота
/stop - Остановка бота
/set - Add a job to the queue
/unset - Remove the job if the user changed their mind"""


@run_async
def start(update, context):
    # update.message.reply_text('Hi!')
    user = update.message.from_user
    logger.info("Пользователь %s начал диалог.", user.first_name)
    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'Привет, <b>{user.first_name} {user.last_name}</b>.',
                             parse_mode=ParseMode.HTML)
    update.message.reply_text(main_menu_message(),
                              reply_markup=main_menu_keyboard())


def help(update, context):
    context.bot.sendMessage(chat_id=update.message.chat_id,
                            text="Поддерживаемые команды:\n%s" % (get_description()))


############################### MAIN MENU ############################################
def main_menu(update, context):
    query = update.callback_query
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text=main_menu_message(),
                                  reply_markup=main_menu_keyboard())


############################### USER'S JOBS PLANNER ############################################
def alarm(context):
    """Send the alarm message."""
    job = context.job
    context.bot.send_message(job.context, text='Beep!')


def set_timer(update, context):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = int(context.args[0])
        if due < 0:
            update.message.reply_text('Sorry we can not go back to future!')
            return

        # Add job to queue and stop current one if there is a timer already
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        new_job = context.job_queue.run_repeating(alarm, due, context=chat_id)
        logger.info(new_job)

        context.chat_data['job'] = new_job

        update.message.reply_text('Timer successfully set!')

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <seconds>')


def unset(update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        update.message.reply_text('You have no active timer')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Timer successfully unset!')


def first_menu(update, context):
    query = update.callback_query
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text=first_menu_message(),
                                  reply_markup=first_menu_keyboard())


def second_menu(update, context):
    query = update.callback_query
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text=second_menu_message(),
                                  reply_markup=second_menu_keyboard())


# and so on for every callback_data option
def first_submenu(update, context):
    pass


def second_submenu(update, context):
    pass


############################### GENERAL SYSTEM COMMAND ############################################
def cancel(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s отменил диалог.", user.first_name)
    update.message.reply_text('Пока! Надеюсь, мы продолжим наше общение завтра',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def unknown(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s ввел некорректную команду.", user.first_name)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Извините, команда не поддерживается."
    )


############################ KEYBOARDS #########################################
def sharing_user_location_keyboard():
    location_keyboard = KeyboardButton(text="Отправить локацию", request_location=True)
    custom_location = [[location_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_location, resize_keyboard=True)
    return reply_markup


def sharing_user_contact_keyboard():
    contact_keyboard = KeyboardButton(text="Отправить контакт", request_contact=True)
    custom_contact = [[contact_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_contact, resize_keyboard=True)
    return reply_markup


def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Начать день', callback_data='m1')],
                [InlineKeyboardButton('Завершить день', callback_data='m2')]]
    return InlineKeyboardMarkup(keyboard)


def first_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Submenu 1-1', callback_data='m1_1')],
                [InlineKeyboardButton('Submenu 1-2', callback_data='m1_2')],
                [InlineKeyboardButton('Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


def second_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Submenu 2-1', callback_data='m2_1')],
                [InlineKeyboardButton('Submenu 2-2', callback_data='m2_2')],
                [InlineKeyboardButton('Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


############################# MESSAGES #########################################
def sharing_user_location():
    return 'Поделись со мной своими координатами.'


def sharing_user_contact():
    return 'Поделись со мной своими контактами.'


def main_menu_message():
    return 'Ура! Еще один день нам подарил Творец!'


def first_menu_message():
    return 'Choose the submenu in first menu:'


def second_menu_message():
    return 'Choose the submenu in second menu:'


############################# ERRORS #########################################
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


############################# HANDLERS #########################################
def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("TOKEN", use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))

    updater.dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
    updater.dispatcher.add_handler(CallbackQueryHandler(first_menu, pattern='m1'))
    updater.dispatcher.add_handler(CallbackQueryHandler(second_menu, pattern='m2'))
    updater.dispatcher.add_handler(CallbackQueryHandler(first_submenu,
                                                        pattern='m1_1'))
    updater.dispatcher.add_handler(CallbackQueryHandler(second_submenu,
                                                        pattern='m2_1'))

    # updater.dispatcher.add_handler(CommandHandler('notify', daily_job, pass_job_queue=True))

    updater.dispatcher.add_handler(CommandHandler("set", set_timer,
                                                  pass_args=True,
                                                  pass_job_queue=True,
                                                  pass_chat_data=True))
    updater.dispatcher.add_handler(CommandHandler("unset", unset, pass_chat_data=True))

    updater.dispatcher.add_handler(CommandHandler("set", set_timer,
                                                  pass_args=True,
                                                  pass_job_queue=True,
                                                  pass_chat_data=True))



    updater.dispatcher.add_handler(CommandHandler('help', help))

    # если введена любая другая команда, которая не поддерживается
    updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.dispatcher.add_handler(CommandHandler('cancel', cancel))

    # log all errors
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()


################################################################################


if __name__ == '__main__':
    main()
