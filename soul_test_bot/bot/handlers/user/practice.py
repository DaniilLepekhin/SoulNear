from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import bot.keyboards.media as kb
from bot.functions.other import check_sub
from bot.loader import dp
import database.repository.media_category as db_media_category
import database.repository.media as db_media


@dp.callback_query(F.data.startswith('media_categories'))
async def media_categories_callback(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Произошла ошибка при попытке удаления сообщения: {e}")
        await call.answer()

    category = call.data.split()[1]

    match category:
        case 'practices':
            text = ("🧘🏼 Ты внутри практик <b>Soul Near</b>.\n\n"
                    "Здесь не дают советов — здесь ты <b>вспоминаешь себя</b>.\n\n"
                    "Выбери, с чем ты хочешь быть сегодня:")

        case 'videos':
            text = ("Этот раздел содержит видео-практики, с ними тебя познакомят наши учителя. "
                    "Заручись их поддержкой и отправляйся в путь к балансу тела и души.")

    categories = await db_media_category.get_all_by_type(category=category)
    await call.message.answer(text=text,
                              reply_markup=kb.categories_menu(categories=categories))


@dp.callback_query(F.data.startswith('media_category'))
async def media_category_callback(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Произошла ошибка при попытке удаления сообщения: {e}")
        await call.answer()

    user_id = call.from_user.id

    if not await check_sub(user_id=user_id):
        return

    category_id = int(call.data.split()[1])
    category = await db_media_category.get(id=category_id)
    medias = await db_media.get_all_by_category(category_id=category_id)

    match category.media_type:
        case 'video':
            await call.message.answer_video(video=category.media_id,
                                            caption=category.text,
                                            reply_markup=kb.medias_menu(medias=medias,
                                                                        category=category.category),
                                            protect_content=True)
        case 'audio':
            await call.message.answer_audio(audio=category.media_id,
                                            caption=category.text,
                                            reply_markup=kb.medias_menu(medias=medias,
                                                                        category=category.category),
                                            protect_content=True)
        case 'photo':
            await call.message.answer_photo(photo=category.media_id,
                                            caption=category.text,
                                            reply_markup=kb.medias_menu(medias=medias,
                                                                        category=category.category),
                                            protect_content=True)
        case None:
            await call.message.answer(text=category.text,
                                      reply_markup=kb.medias_menu(medias=medias,
                                                                  category=category.category),
                                      protect_content=True)


@dp.callback_query(F.data.startswith('media_file'))
async def media_file_callback(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Произошла ошибка при попытке удаления сообщения: {e}")
        await call.answer()

    media_id = int(call.data.split()[1])
    media = await db_media.get(id=media_id)

    match media.media_type:
        case 'video':
            await call.message.answer_video(video=media.media_id,
                                            caption=media.text,
                                            reply_markup=kb.media_menu(category_id=media.category_id),
                                            protect_content=True)
        case 'audio':
            await call.message.answer_audio(audio=media.media_id,
                                            caption=media.text,
                                            reply_markup=kb.media_menu(category_id=media.category_id),
                                            protect_content=True)
        case 'photo':
            await call.message.answer_photo(photo=media.media_id,
                                            caption=media.text,
                                            reply_markup=kb.media_menu(category_id=media.category_id),
                                            protect_content=True)
