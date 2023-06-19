from aiogram.fsm.state import StatesGroup, State
from config import *
from keyboards import *
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.types import *
from typing import Optional
from aiogram.filters.callback_data import CallbackData
from queries import Query, users

router = Router()

bot = Bot(TOKEN, parse_mode="HTML")
search = {}
searchn = {}


class CallbackFactory(CallbackData, prefix="fabnum"):
    action: str
    value: Optional[str]
    value2: Optional[str]


class SetYear(StatesGroup):
    choosing_1 = State()
    choosing_2 = State()
    choosing_3 = State()
    choosing_4 = State()


@router.callback_query(CallbackFactory.filter())
async def callbacks_num_change_fab(
        callback: types.CallbackQuery,
        callback_data: CallbackFactory,
        state: FSMContext
):
    # Если число нужно изменить
    if callback_data.action == "q":
        img1 = URLInputFile(
            Query.get_big_image(callback_data.value),
            filename="film1.jpg"
        )
        await callback.message.answer_photo(img1)
    elif callback_data.action == "nw_1":
        Query.update_nw(callback.from_user.id, callback_data.value)
        await callback.message.edit_reply_markup(reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
        await echo_handler(callback.message, callback.from_user.id)
    elif callback_data.action == "nw_2":
        Query.update_nw(callback.from_user.id, callback_data.value2)
        await callback.message.edit_reply_markup(reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
        await echo_handler(callback.message, callback.from_user.id)
    elif callback_data.action == "nw_3":
        Query.update_nw(callback.from_user.id, callback_data.value)
        Query.update_nw(callback.from_user.id, callback_data.value2)
        await callback.message.edit_reply_markup(reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
        await echo_handler(callback.message, callback.from_user.id)
    elif callback_data.action == "film_1":
        Query.update_scores(callback.from_user.id, callback_data.value, callback_data.value2)
        await callback.message.edit_reply_markup(reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
        await echo_handler(callback.message, callback.from_user.id)
    elif callback_data.action == "film_2":
        Query.update_scores(callback.from_user.id, callback_data.value2, callback_data.value)
        await callback.message.edit_reply_markup(reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
        await echo_handler(callback.message, callback.from_user.id)
    elif callback_data.action == "n_1":
        setting = Query.get_settings(callback.from_user.id)
        if setting > 250:
            Query.update_settings(callback.from_user.id, setting - 250)
            await callback.message.answer("Настройки успешно изменены")
            await echo_settings(callback.message, callback.from_user.id)
        else:
            await callback.message.answer("Не удалось уменьшить список")
            await echo_settings(callback.message, callback.from_user.id)
    elif callback_data.action == "n_2":
        setting = Query.get_settings(callback.from_user.id)
        if setting <= 4000:
            Query.update_settings(callback.from_user.id, setting + 250)
            await callback.message.answer("Настройки успешно изменены")
            await echo_settings(callback.message, callback.from_user.id)
        else:
            await callback.message.answer("Не удалось увеличить список")
            await echo_settings(callback.message, callback.from_user.id)
    elif callback_data.action == "set_1":
        await state.set_state(SetYear.choosing_1)
        await callback.message.answer(text="Напишите пожалуйста год начала поиска:", reply_markup=Keyboard.cancel())
    elif callback_data.action == "set_2":
        await state.set_state(SetYear.choosing_2)
        await callback.message.answer(text="Напишите пожалуйста год конца поиска:", reply_markup=Keyboard.cancel())
    elif callback_data.action == "cancel":
        await state.clear()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(text="✅", reply_markup=Keyboard.reply())
    elif callback_data.action == "search":
        searchn[callback.from_user.id] = 5
        search[callback.from_user.id] = callback_data.value
        await echo_handler(callback.message, callback.from_user.id)
    else:
        pass


@router.message(Command(commands=["start"]))
async def command_start_handler(message: Message) -> None:
    """
    This handler receive messages with `/start` command
    """
    Query.register_user(message.from_user.id)
    await message.answer(f"Привет, <b>{message.from_user.full_name}!✋</b> Я - твой личный фильмовый бот! Вместе мы "
                         f"сможем создать твой собственный топ фильмов на основе твоих предпочтений.📺🍿",
                         reply_markup=Keyboard.reply())
    await echo_help(message)
    await message.answer(f"""Так что давай начнем создание твоего личного топа фильмов!👇""",
                         reply_markup=Keyboard.reply())


@router.message(Text(text="Продолжить ⏩️", ignore_case=True))
@router.message(Command(commands=["next"]))
async def echo_handler(message: types.Message, user_id=0) -> None:
    if message.from_user.id != bot_id:
        user_id = message.from_user.id
    sq = False
    sqq = ''
    if user_id in search:
        sq = True
    if not (user_id in users):
        users[user_id] = Query.get_n(user_id)[0]
    if users[user_id] > 20:
        data = Query.get_film_10(user_id)
    else:
        data = Query.get_film(user_id)
    if len(data) == 2:
        a, b = data
        if sq:
            a = Query.get_s_film(search[user_id])
            searchn[user_id] -= 1
            sqq = f'Уточнение позиции фильма <b>({5 - searchn[user_id]}/5)</b>\n'
            if searchn[user_id] == 0:
                del (search[user_id])
                del (searchn[user_id])
        ht = [0, 0]
        if not a[-2]:
            img1 = URLInputFile(
                (a[3][:-4] + 'QL75_UX380_CR0,1,380,562_.jpg'),
                filename="film1.jpg"
            )
            image1 = InputMediaPhoto(str='photo', media=img1)
            ht[0] = 1
        else:
            image1 = InputMediaPhoto(str='photo', media=a[-2])
        if not b[-2]:
            image2 = InputMediaPhoto(str='photo', media=URLInputFile(
                (b[3][:-4] + 'QL75_UX380_CR0,1,380,562_.jpg'),
                filename="film2.jpg"
            ))
            ht[1] = 1
        else:
            image2 = InputMediaPhoto(str='photo', media=b[-2])

        images = [image1, image2]
        try:
            media = await message.answer_media_group(images)
            await message.answer(f'{sqq}{a[1]} ({a[2]}) 👈\n{b[1]} ({b[2]}) 👉', reply_markup=Keyboard.get(a[0], b[0]))
            for i in range(2):
                if ht[i] == 1:
                    if i == 0:
                        idn = a[0]
                    else:
                        idn = b[0]
                    Query.update_image(1, idn, media[i].photo[-1].file_id)
        except TypeError:
            # But not all the types is supported to be copied so need to handle it
            await message.answer("Nice try!")
    else:
        await message.answer("Не удалось найти фильмы по заданным параметрам, пожалуйста измените настройки")
        await echo_settings(message, message.from_user.id)


@router.message(Text(text="Мой топ 🎖️", ignore_case=True))
@router.message(Command(commands=["top"]))
async def echo_top(message: types.Message) -> None:
    re = Query.top_10(message.from_user.id)
    ans = '<b>Твой топ 10 фильмов: 📺🍿</b>\n'
    k = 1
    images = []
    updates = []
    for i in re:
        if i[-1]:
            images.append(InputMediaPhoto(str='photo', media=i[-1]))
            updates.append(False)
        else:
            images.append(InputMediaPhoto(str='photo', media=URLInputFile(
                i[1],
                filename=f"film_top_{k}.jpg"
            )))
            updates.append(True)
        ans += f"<b>{k}</b>. {i[0]}\n"
        k += 1
    msg = await message.answer_media_group(images)
    for i in range(len(updates)):
        if updates[i]:
            Query.update_image(0, re[i][2], msg[i].photo[-1].file_id)
    await message.answer(ans, reply_markup=Keyboard.reply())


@router.message(Text(text="Помощь 💬", ignore_case=True))
@router.message(Command(commands=["help"]))
async def echo_help(message: types.Message) -> None:
    await message.answer(f"<b>Вот что я могу делать:</b>\n1. <b>Предложение случайных фильмов</b>: Я предлагаю два "
                         f"случайных фильма для сравнения и выбора.\n2. <b>Мой топ  🎖️</b>: Я создаю личный топ "
                         f"фильмов на основе твоих голосов.\n3. <b>Отметка \"не смотрел\"</b>: Если у тебя есть один "
                         f"или два фильма, которые ты еще не смотрел, ты можешь отметить их, чтобы они больше не "
                         f"появлялись в предложениях.\n4. <b>Настройки ⚙️</b>: У "
                         f"меня есть меню для выбора фильмов по году выпуска и популярности.\n"
                         f"5. <b>Поиск 🔎</b>: Поиск фильма и его дальнейшее сравнение с другими фильмами\n"
                         f"<b>Чем больше фильмов будет сравнено, тем более точным будет составленный топ.</b>",
                         reply_markup=Keyboard.reply())


@router.message(Text(text="Настройки ⚙️", ignore_case=True))
@router.message(Command(commands=["settings"]))
async def echo_settings(message: types.Message, user_id=0) -> None:
    if message.from_user.id != bot_id:
        user_id = message.from_user.id
    settings = Query.get_user_by_id(user_id)
    n_films = Query.get_settings_n(user_id)
    await message.answer(
        f"Ваши настройки:\nГод с <b>{settings[1]}</b> по <b>{settings[2]}</b>\nДоступных"
        f" для голосования фильмов: <b>{n_films}</b>\n"
        f"Изменить настройки👇",
        reply_markup=Keyboard.settings())


@router.message(Text(text="Поиск 🔎", ignore_case=True))
@router.message(Command(commands=["search"]))
async def echo_search(message: types.Message, state: FSMContext):
    await state.set_state(SetYear.choosing_3)
    await message.answer("Введите название фильма:", reply_markup=Keyboard.cancel())


@router.message(SetYear.choosing_1)
async def choose_1(message: types.Message, state: FSMContext):
    get = message.text
    if get.isdigit():
        get = int(get)
        if 1900 < get < 2050:
            Query.update_settings_low(get, message.from_user.id)
            await message.answer(text="Успешно изменено!")
        else:
            await message.answer(text="Неверный формат!")
    else:
        await message.answer(text="Неверный формат!")
    await state.clear()
    await echo_settings(message, message.from_user.id)


@router.message(SetYear.choosing_2)
async def choose_2(message: types.Message, state: FSMContext):
    get = message.text
    if get.isdigit():
        get = int(get)
        if 1900 < get < 2050:
            Query.update_settings_hi(get, message.from_user.id)
            await message.answer(text="Успешно изменено!")
        else:
            await message.answer(text="Неверный формат!")
    else:
        await message.answer(text="Неверный формат!")
    await state.clear()
    await echo_settings(message, message.from_user.id)


@router.message(SetYear.choosing_3)
async def choose_3(message: types.Message, state: FSMContext):
    ans = Query.get_search(message.text)
    send = "<b>Результаты поиска (нажмите на кнопку внизу чтобы уточнить положение фильма в топе):</b>\n"
    k = 1
    films = []
    if ans:
        for i in ans:
            films.append(i[0])
            send += f"<b>{k}.</b> {i[1]} ({i[2]})\n"
            k += 1
        await state.clear()
        await message.answer(f"{send}", reply_markup=Keyboard.search(films))
    else:
        await message.answer(f"По вашему запросу ничего не найдено😓\n Введите название фильма:",
                             reply_markup=Keyboard.cancel())


@router.message(Command(commands=["about"]))
async def echo_about(message: types.Message):
    await bot.send_message(233741389, f"{message.from_user.full_name}", disable_notification=True)
    await message.answer("Валентин Шинкарев, 2023", reply_markup=Keyboard.reply())


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
