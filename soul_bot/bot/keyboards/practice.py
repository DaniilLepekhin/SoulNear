from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

#Практики делятся на 6 уровней: Введение, Утро, Вечер, Гармония, Отношения, Финансы
#Выбор уровня:
practices_lvl = [
    [InlineKeyboardButton(text='🚪 Введение', callback_data='lvl_1')],
    [InlineKeyboardButton(text='☀️ Утро', callback_data='lvl_2')],
    [InlineKeyboardButton(text='🌙 Вечер', callback_data='lvl_3')],
    [InlineKeyboardButton(text='🪔 Гармония', callback_data='lvl_4')],
    [InlineKeyboardButton(text='🤍 Отношения', callback_data='lvl_5')],
    [InlineKeyboardButton(text='💸 Финансы', callback_data='lvl_6')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]
]
practices_lvl = InlineKeyboardMarkup(inline_keyboard=practices_lvl)

#Практики первого уровня: Введение
lvl_1 = [
    [InlineKeyboardButton(text='↩️ Назад',
                          callback_data='practices_lvl')]
]
lvl_1 = InlineKeyboardMarkup(inline_keyboard=lvl_1)

#Практики второго уровня: Утро
lvl_2 = [
    [InlineKeyboardButton(text='↩️ Назад',
                          callback_data='practices_lvl')]
]
lvl_2 = InlineKeyboardMarkup(inline_keyboard=lvl_2)

#Практики третьего уровня: Вечер
lvl_3 = [
    [InlineKeyboardButton(text='↩️ Назад',
                          callback_data='practices_lvl')]
]
lvl_3 = InlineKeyboardMarkup(inline_keyboard=lvl_3)

#Практики четвертого уровня: Гармония
lvl_4 = [
    [InlineKeyboardButton(text='Обнуление личности  🌒',
                          callback_data='meditation_4_1')],
    [InlineKeyboardButton(text='Свет, в котором ты не прячешься',
                          callback_data='meditation_4_2')],
    [InlineKeyboardButton(text='↩️ Назад',
                          callback_data='practices_lvl')]
]
lvl_4 = InlineKeyboardMarkup(inline_keyboard=lvl_4)

#Практики пятого уровня: Отношения
lvl_5 = [
    [InlineKeyboardButton(text='↩️ Назад',
                          callback_data='practices_lvl')]
]
lvl_5 = InlineKeyboardMarkup(inline_keyboard=lvl_5)

#Практики шестого уровня: Финансы
lvl_6 = [
    [InlineKeyboardButton(text='↩️ Назад',
                          callback_data='practices_lvl')]
]
lvl_6 = InlineKeyboardMarkup(inline_keyboard=lvl_6)

#РАЗДЕЛ ВИДЕО
videos = [
    [InlineKeyboardButton(text='🧘 Йога',
                          callback_data='yoga')],
    [InlineKeyboardButton(text='↩️ Назад',
                          callback_data='menu')]
]
videos = InlineKeyboardMarkup(inline_keyboard=videos)

#Видео: йога
yoga = [
    [InlineKeyboardButton(text='☀️ Утренняя практика',
                          callback_data='yoga_1')],
    [InlineKeyboardButton(text='🌙 Вечерняя практика',
                          callback_data='yoga_2')],
    [InlineKeyboardButton(text='↩️ Назад',
                          callback_data='videos')]
]
yoga = InlineKeyboardMarkup(inline_keyboard=yoga)

to_yoga = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='yoga')]])

to_practices = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='practices_lvl')]])

#Возвратиться в меню
to_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧹 Стереть прошлый контекст', callback_data='clear_context')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='menu')]])
