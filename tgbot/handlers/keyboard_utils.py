# -*- coding: utf-8 -*-

import copy

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Iterable

from tgbot.handlers import manage_data as md
from tgbot.handlers import static_text as st
from tgbot.models import Favourite


def make_btn_keyboard():
    buttons = [
        [
            InlineKeyboardButton(st.go_back, callback_data=f'{md.BUTTON_BACK_IN_PLACE}'),
        ]
    ]

    return InlineKeyboardMarkup(buttons)


def make_keyboard_for_start_command(poem_id: int = None):
    buttons = [
        [
            InlineKeyboardButton(st.send_again, callback_data=f'{md.SEND_MORE}'),
        ]
    ]
    if poem_id:
        buttons.append([
            InlineKeyboardButton(st.add_to_fav, callback_data=f'{md.ADD_TO_FAV}#{poem_id}'),
            InlineKeyboardButton(st.view_fav, callback_data=f'{md.VIEW_FAV}')
        ])
    else:
        buttons.append([
            InlineKeyboardButton(st.view_fav, callback_data=f'{md.VIEW_FAV}')
        ])

    return InlineKeyboardMarkup(buttons)


def keyboard_confirm_decline_broadcasting():
    buttons = [[
        InlineKeyboardButton(st.confirm_broadcast, callback_data=f'{md.CONFIRM_DECLINE_BROADCAST}{md.CONFIRM_BROADCAST}'),
        InlineKeyboardButton(st.decline_broadcast, callback_data=f'{md.CONFIRM_DECLINE_BROADCAST}{md.DECLINE_BROADCAST}')
    ]]

    return InlineKeyboardMarkup(buttons)


def make_alphabetical_keyboard(alphabet: [str], selected_char: str = None):
    """Получает список букв сортированных по алфавиту и делает из них клавиатуру."""

    buttons = []
    char_index = 0
    button_row = []
    for cur_char in alphabet:
        out_char = f'-{cur_char}-' if cur_char == selected_char else cur_char
        button_row.append(InlineKeyboardButton(out_char, callback_data=f'{md.AUTHOR_BTN}#{cur_char}'))
        char_index += 1
        if char_index % 10 == 0:
            buttons.append(button_row)
            button_row = []
    if button_row:
        buttons.append(button_row)

    buttons.append([
        InlineKeyboardButton(st.go_back, callback_data=f'{md.BUTTON_BACK_IN_PLACE}')
    ])

    return InlineKeyboardMarkup(buttons)


def make_authors_keyboard(authors: [str]):
    """Получает списк авторов и делает из них клавиатуру."""

    buttons = []
    btn_row = []
    i = 1
    for author in authors:
        callback_key = author
        label = author if len(author) <= 30 else f'{author[0:27]}...'
        btn_row.append(InlineKeyboardButton(label, callback_data=f'{md.POEMS_BY_AUTHOR}#{callback_key}'))

        if not i % 3:
            buttons.append(btn_row)
            btn_row = []

        i += 1
    if btn_row:
        buttons.append(btn_row)

    buttons.append([
        InlineKeyboardButton(st.go_back, callback_data=f'{md.BUTTON_BACK_IN_PLACE}')
    ])

    return InlineKeyboardMarkup(buttons)


def make_poems_keyboard(favourites: Iterable[Favourite]):
    """Получает список названий стихов и делает из них клавиатуру."""

    buttons = []
    btn_row = []
    i = 1
    for favourite in favourites:
        label = favourite.poem.header if len(favourite.poem.header) <= 30 else f'{favourite.poem.header[0:27]}...'
        callback_key = favourite.poem.id
        btn_row.append(InlineKeyboardButton(label, callback_data=f'{md.POEM_BY_NAME}#{callback_key}'))

        if not i % 3:
            buttons.append(btn_row)
            btn_row = []

        i += 1
    if btn_row:
        buttons.append(btn_row)

    buttons.append([
        InlineKeyboardButton(st.go_back, callback_data=f'{md.BUTTON_BACK_IN_PLACE}')
    ])

    return InlineKeyboardMarkup(buttons)
