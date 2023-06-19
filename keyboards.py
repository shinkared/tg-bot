from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from main import CallbackFactory


class Keyboard:
    @staticmethod
    def get(a, b):
        builder = InlineKeyboardBuilder()
        builder.button(
            text="👈", callback_data=CallbackFactory(action="film_1", value=a, value2=b)
        )
        builder.button(
            text="👉", callback_data=CallbackFactory(action="film_2", value=a, value2=b)
        )
        builder.button(
            text="Постер в HD", callback_data=CallbackFactory(action="q", value=a)
        )
        builder.button(
            text="Постер в HD", callback_data=CallbackFactory(action="q", value=b)
        )
        builder.button(
            text="Не смотрел(a)", callback_data=CallbackFactory(action="nw_1", value=a, value2=b)
        )
        builder.button(
            text="Не смотрел(a)", callback_data=CallbackFactory(action="nw_2", value=a, value2=b)
        )
        builder.button(
            text="Не смотрел(a) оба", callback_data=CallbackFactory(action="nw_3", value=a, value2=b)
        )
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def new(a, b):
        builder = InlineKeyboardBuilder()
        builder.button(
            text="Постер в HD", callback_data=CallbackFactory(action="q", value=a)
        )
        builder.button(
            text="Постер в HD", callback_data=CallbackFactory(action="q", value=b)
        )
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def settings():
        builder = InlineKeyboardBuilder()
        builder.button(
            text="Год начала", callback_data=CallbackFactory(action="set_1")
        )
        builder.button(
            text="Год конца", callback_data=CallbackFactory(action="set_2")
        )
        builder.button(
            text="Сократить список", callback_data=CallbackFactory(action="n_1")
        )
        builder.button(
            text="Увеличить список", callback_data=CallbackFactory(action="n_2")
        )
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def search(films):
        builder = InlineKeyboardBuilder()
        k = 1
        for i in films:
            builder.button(
                text=f"{k}", callback_data=CallbackFactory(action="search", value=i)
            )
            k += 1
        builder.adjust(k - 1)
        return builder.as_markup()

    @staticmethod
    def cancel():
        builder = InlineKeyboardBuilder()
        builder.button(
            text="Отмена❌", callback_data=CallbackFactory(action="cancel")
        )
        return builder.as_markup()

    @staticmethod
    def reply():
        builder = ReplyKeyboardBuilder()
        builder.button(text="Мой топ 🎖️")
        builder.button(text="Помощь 💬")
        builder.button(text="Поиск 🔎")
        builder.button(text="Настройки ⚙️")
        builder.button(text="Продолжить ⏩️")
        builder.adjust(3)
        return builder.as_markup(resize_keyboard=True)
