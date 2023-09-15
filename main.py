from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, CtxStorage, BaseStateGroup
from dotenv import load_dotenv
import os
import redis
from exchange_rates import get_exchange_rates


ctx = CtxStorage()


class Registration(BaseStateGroup):
    QUESTION = 0
    NO_TOWN_FROM_STATUS = 1
    END = 2


load_dotenv()


KeyboardTown = Keyboard(one_time=True, inline=False)
KeyboardTown.add(Text("Подтверждаю"), color=KeyboardButtonColor.POSITIVE)
KeyboardTown.row()
KeyboardTown.add(Text("Нет"), color=KeyboardButtonColor.NEGATIVE)


KeyboardForRegUser = Keyboard(one_time=True, inline=False)
KeyboardForRegUser.add(Text("Погода"), color=KeyboardButtonColor.PRIMARY)
KeyboardForRegUser.row()
KeyboardForRegUser.add(Text("Пробка"), color=KeyboardButtonColor.POSITIVE)
KeyboardForRegUser.row()
KeyboardForRegUser.add(Text("Афиша"), color=KeyboardButtonColor.PRIMARY)
KeyboardForRegUser.row()
KeyboardForRegUser.add(Text("Валюта"), color=KeyboardButtonColor.POSITIVE)


KeyboardWeather = Keyboard(one_time=True, inline=False)
KeyboardWeather.add(Text("Сегодня"), color=KeyboardButtonColor.PRIMARY)
KeyboardWeather.add(Text("Завтра"), color=KeyboardButtonColor.SECONDARY)
KeyboardWeather.row()
KeyboardWeather.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)

VK_TOKEN = os.getenv('VK_TOKEN')

user_db = redis.Redis(host="localhost", port=6379, db=1)
exchange_rates_db = redis.Redis(host="localhost", port=6379, db=2)

bot = Bot(token=VK_TOKEN)
bot.labeler.vbml_ignore_case = True


@bot.on.private_message(text="начать")
async def get_town(message: Message):
    user_id = message.peer_id

    if user_db.get(user_id):
        await message.answer("Меню:", keyboard=KeyboardForRegUser)
    else:
        user_info = await bot.api.users.get(message.peer_id, "city")
        city_title = user_info[0].city.title
        ctx.set("town", city_title)
        await bot.state_dispenser.set(message.peer_id, Registration.QUESTION)
        await message.answer(f"Вы живете в {city_title} \nЭто ваше место проживание?", keyboard=KeyboardTown)


@bot.on.private_message(state=Registration.QUESTION)
async def question(message: Message):
    if message.text == "Подтверждаю":
        user_id = message.peer_id
        user_db.set(user_id, ctx.get("town"))
        await bot.state_dispenser.set(message.peer_id, Registration.END)
        await message.answer("Регистрация прошла успешно", keyboard=KeyboardForRegUser)


    elif message.text == "Нет":
        await bot.state_dispenser.set(message.peer_id, Registration.NO_TOWN_FROM_STATUS)
        return "Напишите название города в котором вы проживаете"


@bot.on.private_message(state=Registration.NO_TOWN_FROM_STATUS)
async def set_city(message: Message):
    user_id = message.peer_id
    user_db.set(user_id, message.text)
    await bot.state_dispenser.set(message.peer_id, Registration.END)
    await message.answer("Ваше местоположение установлено. Регистрация прошла успешно", keyboard=KeyboardForRegUser)


@bot.on.private_message(text="погода")
async def get_weather(message: Message):
    await message.answer(message="Функция погода", keyboard=KeyboardWeather)


@bot.on.private_message(text="назад")
async def go_back(message: Message):
    await message.answer(message="Функция возвращения", keyboard=KeyboardForRegUser)


@bot.on.private_message(text="валюта")
async def get_inf_rates(message: Message):
    await message.answer(message=f"Доллар: {exchange_rates_db.get('USD').decode('utf-8')}"
                                 f"\nЕвро: {exchange_rates_db.get('EUR').decode('utf-8')}"
                                 f"\nЮань: {exchange_rates_db.get('CNY').decode('utf-8')}"
                                 f"\nЯпонская иена: {exchange_rates_db.get('JPY').decode('utf-8')}"
                                 f"\nБританский фунт стерлингов: {exchange_rates_db.get('GBP').decode('utf-8')}",
                        keyboard=KeyboardForRegUser
                        )


@bot.on.private_message(text="инфо")
async def get_inf(message: Message):
    if user_db.get(message.peer_id):
        city = user_db.get(message.peer_id)
        await message.answer(f"Ваше местоположение установлено в {city.decode('utf-8')}")
    else:
        await message.answer(f"Вы ещё не зарегистрированы")


@bot.on.private_message(text="сброс")
async def del_user_from_db(message: Message):
    if user_db.get(message.peer_id):
        user_db.delete(message.peer_id)
        await message.answer("Вы удалены из бд")
    else:
        await message.answer("Вы ещё не зарегестрированы")


@bot.loop_wrapper.interval(seconds=600)
async def update_exchange_rates():
    exchange_rates_db.set('USD', get_exchange_rates('USD'))
    exchange_rates_db.set('EUR', get_exchange_rates('EUR'))
    exchange_rates_db.set('CNY', get_exchange_rates('CNY'))
    exchange_rates_db.set('JPY', get_exchange_rates('JPY'))
    exchange_rates_db.set('GBP', get_exchange_rates('GBP'))


bot.run_forever()
