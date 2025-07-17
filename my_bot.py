import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# 🔐 ЗАМЕНИ НА СВОЙ ТОКЕН
API_TOKEN = '7214944032:AAGavGZFCbYE_FZKMDAvVxKSdt1PhP4jHno'
# 🔔 ID группы администратора
ADMIN_GROUP_ID = -1002772064995

logging.basicConfig(level=logging.INFO)

# Инициализируем бота с DefaultBotProperties (aiogram 3.21+)
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
# Dispatcher без аргументов
dp = Dispatcher()

# Хранилище данных пользователя и его заказов
user_data = {}     # { user_id: { city, category, item, price } }
user_orders = {}   # { user_id: [ { item, city, price, time, status }, ... ] }

# --- Меню и клавиатуры ---

def start_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🚀 ОТКРЫТЬ МАГАЗИН", callback_data="open_shop"))
    return kb

def city_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("МОСКВА", callback_data="city_Москва"),
        InlineKeyboardButton("САНКТ-ПЕТЕРБУРГ", callback_data="city_Санкт-Петербург"),
        InlineKeyboardButton("⬅ НАЗАД", callback_data="back_start")
    )
    return kb

def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🛍 КАТАЛОГ", callback_data="catalog"),
        InlineKeyboardButton("📦 МОИ ЗАКАЗЫ", callback_data="my_orders"),
        InlineKeyboardButton("🎮 КИНОИГРА", url="https://center-kino.github.io/game_kinoshlep/"),
        InlineKeyboardButton("👤 ПОМОЩЬ", url="https://t.me/PRdemon")
    )
    return kb

def catalog_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("👕 ФУТБОЛКИ", callback_data="category_tshirts"),
        InlineKeyboardButton("🧢 КЕПКИ", callback_data="category_caps"),
        InlineKeyboardButton("🧥 ТОЛСТОВКИ", callback_data="category_hoodies"),
        InlineKeyboardButton("🎲 НАСТОЛЬНАЯ ИГРА", callback_data="category_game"),
        InlineKeyboardButton("⬅ НАЗАД", callback_data="main")
    )
    return kb

def product_menu(category: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    items = {
        "tshirts": ["РЕЖИССЕР", "ОРИГИНАЛ", "СЦЕНАРИЙ"],
        "caps":    ["ЦК", "ЭПИЗОД", "КИНОШЛЕПКА"],
        "hoodies": ["ХУДИ 1", "ХУДИ 2", "ХУДИ 3"],
        "game":    ["СНИМИ ЕСЛИ СМОЖЕШЬ"]
    }
    for idx, name in enumerate(items[category]):
        kb.add(InlineKeyboardButton(name, callback_data=f"product_{category}_{idx}"))
    kb.add(InlineKeyboardButton("⬅ НАЗАД", callback_data="catalog"))
    return kb

def confirm_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💳 КУПИТЬ", callback_data="buy"),
        InlineKeyboardButton("⬅ НАЗАД", callback_data="catalog")
    )
    return kb

def payment_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("✅ Я ОПЛАТИЛ", callback_data="paid"),
        InlineKeyboardButton("❌ ОТМЕНА", callback_data="main")
    )
    return kb

def after_payment_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main"),
        InlineKeyboardButton("📦 УЗНАТЬ СТАТУС", callback_data="order_status")
    )
    return kb

# --- Хендлеры ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer(
        "🔓 Добро пожаловать! Нажми кнопку, чтобы открыть магазин:",
        reply_markup=start_menu()
    )

@dp.callback_query()
async def cb_handler(c: types.CallbackQuery):
    data = c.data
    uid = c.from_user.id
    chat_id = c.message.chat.id

    # Удаляем старое сообщение
    try:
        await bot.delete_message(chat_id, c.message.message_id)
    except:
        pass

    # Навигация
    if data == "open_shop":
        await c.message.answer("🏙️ Выберите ваш город:", reply_markup=city_menu())

    elif data.startswith("city_"):
        city = data.split("_", 1)[1]
        user_data[uid]["city"] = city
        await c.message.answer(
            f"📍 Город: *{city}*\n\nВы в главном меню:",
            reply_markup=main_menu()
        )

    elif data == "back_start":
        await c.message.answer("🔓 Нажми, чтобы открыть магазин:", reply_markup=start_menu())

    elif data == "main":
        await c.message.answer("📲 Главное меню:", reply_markup=main_menu())

    elif data == "catalog":
        await c.message.answer("📂 Выберите категорию:", reply_markup=catalog_menu())

    elif data.startswith("category_"):
        category = data.split("_", 1)[1]
        user_data[uid]["category"] = category
        await c.message.answer("🛍 Выберите товар:", reply_markup=product_menu(category))

    elif data.startswith("product_"):
        _, category, idx_str = data.split("_")
        idx = int(idx_str)
        names = {
            "tshirts": ["РЕЖИССЕР", "ОРИГИНАЛ", "СЦЕНАРИЙ"],
            "caps":    ["ЦК", "ЭПИЗОД", "КИНОШЛЕПКА"],
            "hoodies": ["ХУДИ 1", "ХУДИ 2", "ХУДИ 3"],
            "game":    ["СНИМИ ЕСЛИ СМОЖЕШЬ"]
        }
        name = names[category][idx]
        price = 2200
        user_data[uid].update(item=name, price=price)
        city = user_data[uid].get("city", "—")
        await c.message.answer(
            f"*{name}*\n\nОписание: оверсайз, футер 3 нитки\n💰 *Цена*: {price}₽\n🏙 *Город*: {city}",
            reply_markup=confirm_menu()
        )

    elif data == "buy":
        await c.message.answer(
            "💳 Для оплаты переведите на:\n*8-915-087-97-98* (Владимир Ф)\n"
            "Тинькофф или Сбер.\n\nПосле перевода нажмите “✅ Я ОПЛАТИЛ”",
            reply_markup=payment_menu()
        )

    elif data == "paid":
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        item = user_data[uid]["item"]
        price = user_data[uid]["price"]
        city = user_data[uid]["city"]
        mention = c.from_user.get_mention()

        order = {"item": item, "price": price, "city": city, "time": now, "status": "pending"}
        user_orders.setdefault(uid, []).append(order)
        order_idx = len(user_orders[uid]) - 1

        await c.message.answer("🕓 Ваш заказ принят! Ожидайте подтверждения.", reply_markup=after_payment_menu())

        admin_text = (
            f"📥 *НОВЫЙ ЗАКАЗ*\n"
            f"Пользователь: {mention}\nГород: {city}\n"
            f"Товар: {item}\nЦена: {price}₽\nВремя: {now}"
        )
        admin_kb = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("✅ ОПЛАЧЕНО", callback_data=f"admin_paid_{uid}_{order_idx}"),
            InlineKeyboardButton("❌ НЕ ОПЛАЧЕНО", callback_data=f"admin_unpaid_{uid}_{order_idx}")
        )
        await bot.send_message(ADMIN_GROUP_ID, admin_text, reply_markup=admin_kb)

    elif data.startswith("admin_paid_") or data.startswith("admin_unpaid_"):
        _, action, uid_str, idx_str = data.split("_")
        target_uid, idx = int(uid_str), int(idx_str)
        order = user_orders[target_uid][idx]
        if action == "paid":
            order["status"] = "paid"
            await bot.send_message(target_uid, f"✅ Ваш заказ «{order['item']}» подтверждён!")
        else:
            order["status"] = "unpaid"
            await bot.send_message(target_uid, f"❌ Ваш заказ «{order['item']}» не подтверждён. Пришлите чек.")
        # скрываем кнопки в сообщении админа
        await bot.edit_message_reply_markup(
            chat_id=ADMIN_GROUP_ID,
            message_id=c.message.message_id,
            reply_markup=None
        )

    elif data == "my_orders":
        orders = user_orders.get(uid, [])
        if not orders:
            text = "📭 У вас пока нет заказов."
        else:
            text = "📦 *Ваши заказы:*\n"
            for i, o in enumerate(orders, start=1):
                emoji = {"pending": "⏳", "paid": "✅", "unpaid": "❌"}[o["status"]]
                text += f"\n{i}. {o['item']} — {o['price']}₽ ({o['time']}) {emoji}"
        await c.message.answer(text, reply_markup=main_menu())

    elif data == "order_status":
        await c.message.answer(
            "🔄 Статус заказа можно посмотреть в разделе “📦 МОИ ЗАКАЗЫ”.",
            reply_markup=main_menu()
        )

    else:
        await c.message.answer("📲 Главное меню:", reply_markup=main_menu())

# --- Запуск бота ---

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
