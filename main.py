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

# Инициализация бота
router = Router()

bot = Bot(TOKEN, parse_mode="HTML")

# Хранение информации о поиске
search = {}  # Найденный фильм
searchn = {}  # Оставшиеся разы уточнения


# Класс хранящий информацию колбека
class CallbackFactory(CallbackData, prefix="cb"):
    action: str
    value: Optional[str]
    value2: Optional[str]


# Различные статусы пользователя
class States(StatesGroup):
    """
    Различные статусы действия пользователя

    first_year - выбор года начала поиска

    last_year - выбор года конца поиска

    film_name_enter - написание строки поиска
    """
    first_year = State()
    last_year = State()
    film_name_enter = State()


@router.callback_query(CallbackFactory.filter())
async def callbacks_fb(
        callback: types.CallbackQuery,
        callback_data: CallbackFactory,
        state: FSMContext
):
    match callback_data.action:
        # Получение фото в хорошем качестве
        case "q":
            img1 = URLInputFile(
                Query.get_big_image(callback_data.value),
                filename="film1.jpg"
            )
            await callback.message.answer_photo(img1)
        # Не просмотрен левый фильм
        case "nw_1":
            Query.update_nw(callback.from_user.id, callback_data.value)
            await callback.message.edit_reply_markup(
                reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
            await echo_handler(callback.message, callback.from_user.id)
        # Не просмотрен правый фильм
        case "nw_2":
            Query.update_nw(callback.from_user.id, callback_data.value2)
            await callback.message.edit_reply_markup(
                reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
            await echo_handler(callback.message, callback.from_user.id)
        # Не просмотрены оба фильма
        case "nw_3":
            Query.update_nw(callback.from_user.id, callback_data.value)
            Query.update_nw(callback.from_user.id, callback_data.value2)
            await callback.message.edit_reply_markup(
                reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
            await echo_handler(callback.message, callback.from_user.id)
        # Понравился левый фильм
        case "film_1":
            Query.update_scores(callback.from_user.id, callback_data.value, callback_data.value2)
            await callback.message.edit_reply_markup(
                reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
            await echo_handler(callback.message, callback.from_user.id)
        # Понравился правый фильм
        case "film_2":
            Query.update_scores(callback.from_user.id, callback_data.value2, callback_data.value)
            await callback.message.edit_reply_markup(
                reply_markup=Keyboard.new(callback_data.value, callback_data.value2))
            await echo_handler(callback.message, callback.from_user.id)
        # Запись минимального года
        case "n_1":
            setting = Query.get_settings(callback.from_user.id)
            if setting > 250:
                Query.update_settings(callback.from_user.id, setting - 250)
                await callback.message.answer("Настройки успешно изменены")
                await echo_settings(callback.message, callback.from_user.id)
            else:
                await callback.message.answer("Не удалось уменьшить список")
                await echo_settings(callback.message, callback.from_user.id)
        # Запись максимального года
        case "n_2":
            setting = Query.get_settings(callback.from_user.id)
            if setting <= 4000:
                Query.update_settings(callback.from_user.id, setting + 250)
                await callback.message.answer("Настройки успешно изменены")
                await echo_settings(callback.message, callback.from_user.id)
            else:
                await callback.message.answer("Не удалось увеличить список")
                await echo_settings(callback.message, callback.from_user.id)
        # Настройки минимального года
        case "set_1":
            await state.set_state(States.first_year)
            await callback.message.answer(text="Напишите пожалуйста год начала поиска:", reply_markup=Keyboard.cancel())
        # Настройки максимального года
        case "set_2":
            await state.set_state(States.last_year)
            await callback.message.answer(text="Напишите пожалуйста год конца поиска:", reply_markup=Keyboard.cancel())
        # Снятие статусов
        case "cancel":
            await state.clear()
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(text="✅", reply_markup=Keyboard.reply())
        # Уточнение по поиску
        case "search":
            searchn[callback.from_user.id] = 5
            search[callback.from_user.id] = callback_data.value
            await echo_handler(callback.message, callback.from_user.id)


@router.message(Command(commands=["start"]))
async def command_start_handler(message: Message) -> None:
    """
    Вывод сообщения команды /start
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
    """
    Вывод двух фильмов пользователю
    """
    # Костыль для передачи user_id по вызову
    # Если вызвать echo_handler с колбека, message будет от бота (теряется user_id)
    if message.from_user.id != bot_id:
        user_id = message.from_user.id

    # Проверка на уточнение сравнения
    is_approximating = False
    message_text = ''
    if user_id in search:
        is_approximating = True

    # Количество оцененных фильмов пользователем
    if not (user_id in users):
        users[user_id] = Query.get_n(user_id)[0]

    # Если оценок более 20, то используется более сложная формула для получения фильмов
    if users[user_id] > 20:
        films = Query.get_film_10(user_id)
    else:
        films = Query.get_film(user_id)

    if len(films) == 2:
        if is_approximating:
            films[0] = Query.get_s_film(search[user_id])
            searchn[user_id] -= 1
            message_text = f'Уточнение позиции фильма <b>({5 - searchn[user_id]}/5)</b>\n'
            # Очистка поиска после того как фильм был оценен последний раз
            if searchn[user_id] == 0:
                del (search[user_id])
                del (searchn[user_id])
        is_uploaded = [False, False]  # Загружался ли файл на сервер телеграма
        images = []

        # Создание медиа-группы
        for i in range(2):
            if not films[i][-2]:
                img1 = URLInputFile(
                    (films[i][3][:-4] + 'QL75_UX380_CR0,1,380,562_.jpg'),
                    filename=f"film{i}.jpg"
                )
                images.append(InputMediaPhoto(str='photo', media=img1))
                is_uploaded[i] = True
            else:
                images.append(InputMediaPhoto(str='photo', media=films[i][-2]))

        try:
            media = await message.answer_media_group(images)
            await message.answer(f'{message_text}{films[0][1]} ({films[0][2]}) 👈\n{films[1][1]} ({films[1][2]}) 👉',
                                 reply_markup=Keyboard.get(films[0][0], films[1][0]))

            # Запись id файла в бд
            for i in range(2):
                if is_uploaded[i]:
                    if i == 0:
                        idn = films[0][0]
                    else:
                        idn = films[1][0]
                    Query.update_image(1, idn, media[i].photo[-1].file_id)

        except TypeError:
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
    await state.set_state(States.film_name_enter)
    await message.answer("Введите название фильма:", reply_markup=Keyboard.cancel())


@router.message(States.first_year)
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


@router.message(States.last_year)
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


@router.message(States.film_name_enter)
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
