# -*- coding: utf-8 -*-

"""Головная логика бота."""

import logging
import requests

from bs4 import BeautifulSoup
from random import randint
from typing import Iterable, Optional

from tgbot.handlers import static_text as st
from tgbot.models import Favourite, Poem, User

logger = logging.getLogger('default')


class Poetry:
    source = 'https://www.culture.ru/literature/poems'
    source_domain = 'https://www.culture.ru'

    def __init__(self, user: User):
        self.user = user

    def load_poem(self, id: int = None) -> (str, Optional[int]):
        """Загружает стих.

        Если передан id, то стих выбирается из базы, иначе - загружается случайный с сайта.
        """

        result = ''
        poem_id = None

        try:
            if id:
                poem = Poem.objects.get(pk=id)
                result = self.format_poem(poem)
                poem_id = id
            else:
                # 1. Находим максимальную страничку со стихами
                response = requests.get(self.source)
                html = BeautifulSoup(response.text, 'lxml')
                last_page = int(html.select('nav.pagination a')[-1].get_text())

                # 2. Выбираем случайную страничку откуда будем брать сейчас стих
                random_page = randint(1, last_page)
                url = f'https://www.culture.ru/literature/poems?page={random_page}&limit=45&query='
                response = requests.get(url)
                html = BeautifulSoup(response.text, 'lxml')
                poem_links = html.select('.card-heading_title-link')

                # 3. Выбираем случайный стих
                random_poem = randint(0, len(poem_links))
                poem_link = poem_links[random_poem].get('href')
                url = f'{self.source_domain}{poem_link}'
                response = requests.get(url)
                html = BeautifulSoup(response.text, 'lxml')

                # 4. Готовим стих к сохранению в БД
                author = html.select_one('.entity-heading_subtitle').get_text()
                poem_name = html.select_one('.entity-heading_title').get_text()
                poem_paragraphs = html.select('.content-columns_block p')
                poem_text = []
                for paragraph in poem_paragraphs:
                    poem_text.append(str(paragraph).replace('<br/>', '\n').replace('<p>', '').replace('</p>', ''))
                poem_text = "\n\n".join(poem_text)

                poem_db, _ = Poem.objects.get_or_create(author=author, header=poem_name, text=poem_text)
                poem_id = poem_db.id

                result = self.format_poem(poem_db)
        except Exception as ex:
            logger.error(f'Ошибка в процессе загрузки стиха: {ex}')
            result = f'{st.error}\n{ex}'

        return result, poem_id

    def add_to_fav(self, id: int) -> None:
        """Добавляет стих в избранное."""

        poem = Poem.objects.get(pk=id)
        Favourite.objects.get_or_create(user=self.user, poem=poem)

    def get_authors(self, only_first_chars: bool = False, **kwargs) -> [str]:
        """Возврщает список авторов стихов из избранного пользователя.

        Если передан флаг only_first_chars, то вернут только первые буквы в фамилиях автора.
        """

        filter_by_first_char = kwargs.get('last_name_first_char')
        filter = {
            'user': self.user,
        }
        if filter_by_first_char:
            filter['poem__author__contains'] = f' {filter_by_first_char}'

        authors = Favourite.objects.\
            filter(**filter).\
            values('poem__author').\
            order_by('poem__author').\
            distinct()

        if only_first_chars:
            result = set()
            for author in authors:
                result.add(author['poem__author'].split()[1][0])
        else:
            result = [author['poem__author'].split()[1] for author in authors]

        result = list(result)
        result.sort()
        return result

    def get_poems(self, author: str) -> Iterable[Favourite]:
        """Получает автора. Возвращает стихи из избранного этого автора."""

        return Favourite.objects.filter(user=self.user, poem__author__contains=author).order_by('poem__header')

    def get_poem_by_id(self, poem_id: str) -> Poem:
        return Poem.objects.get(pk=poem_id)

    @staticmethod
    def format_poem(poem: Poem) -> str:
        """Возвращает стих в Markdown-ready состоянии."""

        return f'*{poem.header}*\n\n{poem.text}\n\n_{poem.author}_'
