# -*- coding: utf-8 -*-

import datetime
import logging
import telegram

from django.utils import timezone

from tgbot.handlers import commands
from tgbot.handlers import static_text as st
from tgbot.handlers import manage_data as md
from tgbot.handlers import keyboard_utils as kb
from tgbot.handlers.utils import handler_logging
from tgbot.models import User
from tgbot.poetry import Poetry
from tgbot.tasks import broadcast_message
from tgbot.utils import convert_2_user_time, extract_user_data_from_update, get_chat_id

logger = logging.getLogger('default')


@handler_logging()
def send_more(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    user = User.get_user(update, context)

    poetry = Poetry(user)
    poem_text, poem_id = poetry.load_poem()

    context.bot.edit_message_text(
        text=poem_text,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.make_keyboard_for_start_command(poem_id),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


@handler_logging()
def add_to_fav(update, context):
    logger.info('Начинаем процесс добавления в избранное')
    user_id = extract_user_data_from_update(update)['user_id']
    user = User.get_user(update, context)

    # Извлекаем ID стиха из колбека
    query = update.callback_query
    query.answer()
    query_data = query.data.split('#')
    poem_id = query_data[1]
    logger.info(f'Добавляем в избранное стих #{poem_id}')

    poetry = Poetry(user)
    poetry.add_to_fav(poem_id)
    msg = st.add_to_fav_success

    context.bot.edit_message_text(
        text=msg,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.make_keyboard_for_start_command(poem_id),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


@handler_logging()
def view_fav(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    user = User.get_user(update, context)

    poetry = Poetry(user)
    authors_first_chars = poetry.get_authors(only_first_chars=True)

    markup = kb.make_alphabetical_keyboard(authors_first_chars)

    context.bot.edit_message_text(
        text=st.choose_author,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=markup,
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


@handler_logging()
def show_authors(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    user = User.get_user(update, context)

    query = update.callback_query
    query.answer()
    query_data = query.data.split('#')
    selected_char = query_data[1]

    poetry = Poetry(user)
    authors = poetry.get_authors(only_first_chars=False, last_name_first_char=selected_char)

    context.bot.edit_message_text(
        text=st.choose_author_full,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.make_authors_keyboard(authors),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


@handler_logging()
def show_author_poems(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    user = User.get_user(update, context)

    query = update.callback_query
    query.answer()
    query_data = query.data.split('#')
    author = query_data[1]

    poetry = Poetry(user)
    poems = poetry.get_poems(author)
    logger.info(poems)

    context.bot.edit_message_text(
        text=st.choose_poem,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.make_poems_keyboard(poems),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


@handler_logging()
def show_poem_by_id(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    user = User.get_user(update, context)

    query = update.callback_query
    query.answer()
    query_data = query.data.split('#')
    poem_id = query_data[1]

    poetry = Poetry(user)
    poem = poetry.get_poem_by_id(poem_id)

    context.bot.edit_message_text(
        text=poetry.format_poem(poem),
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.make_btn_keyboard(),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


@handler_logging()
def back_to_main_menu_handler(update, context):  # callback_data: BUTTON_BACK_IN_PLACE variable from manage_data.py
    user, created = User.get_user_and_created(update, context)

    payload = context.args[0] if context.args else user.deep_link  # if empty payload, check what was stored in DB
    text = st.welcome

    user_id = extract_user_data_from_update(update)['user_id']
    context.bot.edit_message_text(
        chat_id=user_id,
        text=text,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.make_keyboard_for_start_command(),
        parse_mode=telegram.ParseMode.MARKDOWN
    )


@handler_logging()
def secret_level(update, context): #callback_data: SECRET_LEVEL_BUTTON variable from manage_data.py
    """ Pressed 'secret_level_button_text' after /start command"""
    user_id = extract_user_data_from_update(update)['user_id']
    text = "Congratulations! You've opened a secret room👁‍🗨. There is some information for you:\n" \
           "*Users*: {user_count}\n" \
           "*24h active*: {active_24}".format(
            user_count=User.objects.count(),
            active_24=User.objects.filter(updated_at__gte=timezone.now() - datetime.timedelta(hours=24)).count()
    )

    context.bot.edit_message_text(
        text=text,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=telegram.ParseMode.MARKDOWN
    )


def broadcast_decision_handler(update, context): #callback_data: CONFIRM_DECLINE_BROADCAST variable from manage_data.py
    """ Entered /broadcast <some_text>.
        Shows text in Markdown style with two buttons:
        Confirm and Decline
    """
    broadcast_decision = update.callback_query.data[len(md.CONFIRM_DECLINE_BROADCAST):]
    entities_for_celery = update.callback_query.message.to_dict().get('entities')
    entities = update.callback_query.message.entities
    text = update.callback_query.message.text
    if broadcast_decision == md.CONFIRM_BROADCAST:
        admin_text = st.msg_sent,
        user_ids = list(User.objects.all().values_list('user_id', flat=True))
        broadcast_message.delay(user_ids=user_ids, message=text, entities=entities_for_celery)
    else:
        admin_text = text

    context.bot.edit_message_text(
        text=admin_text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        entities=None if broadcast_decision == md.CONFIRM_BROADCAST else entities
    )