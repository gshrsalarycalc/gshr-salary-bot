import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# --- КОНФІГУРАЦІЯ ---
BOT_TOKEN = "8885493656:AAGOLCjNrgaWa0yLPIcDooOOXy-aEVkGMg8"

BRON_TARGET = 20200.0         # Необхідна сума на бронь
BASE_DAILY_RATE = 1800.0     # Оплата за добу (24 год)
HOURLY_RATE = BASE_DAILY_RATE / 24.0  # 75 грн/год

# Ставки підробітків за 12 годин
MINE_RATE_12H = 550.0
CCTV_RATE_12H = 610.0

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- СТАНИ (FSM) ---
class CalcState(StatesGroup):
    shifts_17 = State()
    shifts_7 = State()
    driver_shifts = State()
    years_exp = State()
    bonuses = State()
    penalties = State()

# --- КЛАВІАТУРИ ---
start_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🧮 Порахувати зарплату")]],
    resize_keyboard=True
)

# --- ХЕНДЛЕРИ ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Привіт! Це твій помічник для розрахунку зарплати ГШР та перевірки броні.\n\n"
        "💡 *Як користуватися:* просто натисни кнопку нижче і відповідай на прості запитання бота (вводь звичайні цифри з клавіатури).\n"
        "Якщо чогось немає (наприклад, штрафів або премій) — просто пиши цифру **0**.",
        reply_markup=start_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text == "🧮 Порахувати зарплату")
async def start_calc(message: Message, state: FSMContext):
    await state.set_state(CalcState.shifts_17)
    await message.answer(
        "📌 **Крок 1 з 6**\n"
        "Подивись у свій графік в Excel і порахуй, скільки у тебе було **змін по 17 годин** за місяць.\n"
        "👉 Введи це число цифрами (наприклад: `10`):",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )

@dp.message(CalcState.shifts_17)
async def process_17(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Будь ласка, введи звичайне ціле число (наприклад, 5 або 0):")
    await state.update_data(shifts_17=int(message.text))
    await state.set_state(CalcState.shifts_7)
    await message.answer(
        "📌 **Крок 2 з 6**\n"
        "Тепер порахуй за графіком, скільки у тебе було **змін по 7 годин**.\n"
        "👉 Введи число (якщо таких не було, введи `0`):",
        parse_mode="Markdown"
    )

@dp.message(CalcState.shifts_7)
async def process_7(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Потрібно ввести цифру! Спробуй ще раз:")
    await state.update_data(shifts_7=int(message.text))
    await state.set_state(CalcState.driver_shifts)
    await message.answer(
        "📌 **Крок 3 з 6**\n"
        "🚗 Уточнимо щодо доплати водію (+100 грн за кожну зміну водієм).\n"
        "👉 **Скільки змін у вас було водієм?** (якщо не працював водієм, введи `0`):",
        parse_mode="Markdown"
    )

@dp.message(CalcState.driver_shifts)
async def process_driver_shifts(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Будь ласка, введи кількість змін цифрами (або 0):")
    await state.update_data(driver_shifts=int(message.text))
    await state.set_state(CalcState.years_exp)
    await message.answer(
        "📌 **Крок 4 з 6**\n"
        "⭐ Доплата за стаж (+50 грн за кожний рік за добу/24 години, максимум до 5 років / 250 грн).\n"
        "👉 Введи свій **стаж роботи у роках** (цілим числом від 0 до 5. Якщо стаж більше 5 років — все одно пиши `5`):",
        parse_mode="Markdown"
    )

@dp.message(CalcState.years_exp)
async def process_exp(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Введи число від 0 до 5:")
    exp = min(max(0, int(message.text)), 5)
    await state.update_data(years_exp=exp)
    await state.set_state(CalcState.bonuses)
    await message.answer(
        "📌 **Крок 5 з 6**\n"
        "🎁 Чи були у тебе премії? (Кожна премія = +500 грн).\n"
        "👉 Скільки всього було **премій** за місяць? (якщо не було, введи `0`):",
        parse_mode="Markdown"
    )

@dp.message(CalcState.bonuses)
async def process_bonuses(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Введи кількість премій цифрами (або 0):")
    await state.update_data(bonuses=int(message.text))
    await state.set_state(CalcState.penalties)
    await message.answer(
        "📌 **Крок 6 з 6**\n"
        "❌ Чи були штрафи? (Кожен штраф = -500 грн).\n"
        "👉 Скільки всього було **штрафів** за місяць? (якщо штрафів не було, обов'язково введи `0`):",
        parse_mode="Markdown"
    )

@dp.message(CalcState.penalties)
async def process_penalties(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Введи кількість штрафів цифрами (або 0):")
    
    data = await state.get_data()
    penalties = int(message.text)
    
    # Отримання даних
    s17 = data['shifts_17']
    s7 = data['shifts_7']
    driver_shifts = data['driver_shifts']
    years_exp = data['years_exp']
    bonuses = data['bonuses']
    
    # --- Розрахунки ---
    total_hours = (s17 * 17) + (s7 * 7)
    full_shifts_eq = total_hours / 24.0
    
    base_pay = total_hours * HOURLY_RATE
    driver_bonus = driver_shifts * 100.0  # Фіксована доплата: 100 грн * кількість змін
    exp_bonus = (years_exp * 50.0) * full_shifts_eq
    total_bonuses = bonuses * 500.0
    total_penalties = penalties * 500.0
    
    total_earned = base_pay + driver_bonus + exp_bonus + total_bonuses - total_penalties
    
    # --- Формування відповіді ---
    res = []
    res.append("📊 **РЕЗУЛЬТАТИ РОЗРАХУНКУ (ГШР)**\n")
    res.append(f"• Відпрацьовано годин: **{total_hours} год.** ({full_shifts_eq:.1f} доби)")
    res.append(f"• Базова оплата: **{base_pay:,.2f} грн**")
    
    if driver_shifts > 0:
        res.append(f"• Доплата водія ({driver_shifts} зм. × 100): **+{driver_bonus:,.2f} грн**")
    if years_exp > 0:
        res.append(f"• Доплата за стаж ({years_exp}р): **+{exp_bonus:,.2f} грн**")
    if bonuses > 0:
        res.append(f"• Премії ({bonuses} шт): **+{total_bonuses:,.2f} грн**")
    if penalties > 0:
        res.append(f"• Штрафи ({penalties} шт): **-{total_penalties:,.2f} грн**")
        
    res.append("----------------------------------")
    res.append(f"💰 **РАЗОМ ЗАРОБІТОК:** `{total_earned:,.2f} грн`")
    res.append(f"🛡️ **МЕТА НА БРОНЬ:** `{BRON_TARGET:,.2f} грн`")
    res.append("----------------------------------\n")
    
    if total_earned >= BRON_TARGET:
        surplus = total_earned - BRON_TARGET
        res.append(f"✅ **ГРОШЕЙ ВИСТАЧАЄ НА БРОНЬ!**")
        res.append(f"💡 Фінансовий запас: **+{surplus:,.2f} грн**")
    else:
        deficit = BRON_TARGET - total_earned
        res.append(f"❌ **ГРОШЕЙ НЕ ВИСТАЧАЄ НА БРОНЬ**")
        res.append(f"⚠️ Дефіцит: **{deficit:,.2f} грн**\n")
        
        shifts_mine_needed = -(-deficit // MINE_RATE_12H)
        shifts_cctv_needed = -(-deficit // CCTV_RATE_12H)
        
        res.append("🛠️ **Рекомендації щодо підробітку:**")
        res.append(f"• На **шахті** (12 год. = 550 грн): потрібно відпрацювати приблизно **{int(shifts_mine_needed)} змін(и)**")
        res.append(f"• На **відеоспостереженні** (12 год. = 610 грн): потрібно відпрацювати приблизно **{int(shifts_cctv_needed)} змін(и)**")

    await message.answer("\n".join(res), reply_markup=start_kb, parse_mode="Markdown")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())