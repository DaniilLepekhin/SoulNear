"""
📊 Скрипт для генерации отчета по конверсии воронок

Использование:
    python analytics_report.py

Показывает статистику по всем рекламным ссылкам:
- Количество переходов
- Конверсия в квиз
- Конверсия в активацию подарка
- Конверсия в retention
- Конверсия в покупку
"""

import asyncio
from datetime import datetime
from sqlalchemy import select, func, case
from database.database import db
from database.models.deeplink_event import DeeplinkEvent
from database.models.quiz_session import QuizSession
from database.models.user import User


async def get_funnel_stats():
    """Получить статистику по всем воронкам"""

    async with db() as session:
        # Основной запрос со всеми метриками
        query = (
            select(
                DeeplinkEvent.raw_link.label('link'),
                func.count(func.distinct(DeeplinkEvent.user_id)).label('transitions'),
                func.count(func.distinct(
                    case((QuizSession.id.isnot(None), DeeplinkEvent.user_id))
                )).label('started_quiz'),
                func.count(func.distinct(
                    case((QuizSession.status == 'completed', DeeplinkEvent.user_id))
                )).label('completed_quiz'),
                func.count(func.distinct(
                    case((User.free_messages_activated == True, DeeplinkEvent.user_id))
                )).label('activated_gift'),
                func.count(func.distinct(
                    case((User.last_retention_sent.isnot(None), DeeplinkEvent.user_id))
                )).label('got_retention'),
                func.count(func.distinct(
                    case((User.sub_date > datetime.now(), DeeplinkEvent.user_id))
                )).label('bought_subscription'),
            )
            .select_from(DeeplinkEvent)
            .outerjoin(QuizSession, DeeplinkEvent.quiz_session_id == QuizSession.id)
            .outerjoin(User, DeeplinkEvent.user_id == User.user_id)
            .where(DeeplinkEvent.raw_link.in_([
                'analysis_relationships_ads',
                'analysis_money_ads',
                'analysis_purpose_ads'
            ]))
            .group_by(DeeplinkEvent.raw_link)
            .order_by(func.count(func.distinct(DeeplinkEvent.user_id)).desc())
        )

        result = await session.execute(query)
        rows = result.fetchall()

        return rows


def calculate_conversion(value, total):
    """Рассчитать конверсию в %"""
    if total == 0:
        return 0.0
    return round(100.0 * value / total, 1)


def print_funnel_report(stats):
    """Вывести красивый отчет"""

    print("\n" + "="*100)
    print("📊 ОТЧЕТ ПО КОНВЕРСИИ РЕКЛАМНЫХ ВОРОНОК")
    print("="*100)
    print(f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100 + "\n")

    # Названия воронок
    funnel_names = {
        'analysis_relationships_ads': '❤️  Отношения',
        'analysis_money_ads': '💰 Деньги',
        'analysis_purpose_ads': '🎯 Предназначение'
    }

    for row in stats:
        link = row.link
        name = funnel_names.get(link, link)

        print(f"\n{'='*100}")
        print(f"  {name}")
        print(f"  Ссылка: https://t.me/SoulnearBot?start={link}")
        print(f"{'='*100}")

        print(f"\n  📈 ВОРОНКА:")
        print(f"     1️⃣  Переходов по ссылке:        {row.transitions:>6}")
        print(f"     2️⃣  Начали квиз:               {row.started_quiz:>6}  ({calculate_conversion(row.started_quiz, row.transitions):>5}%)")
        print(f"     3️⃣  Завершили квиз:            {row.completed_quiz:>6}  ({calculate_conversion(row.completed_quiz, row.transitions):>5}%)")
        print(f"     4️⃣  Активировали подарок:      {row.activated_gift:>6}  ({calculate_conversion(row.activated_gift, row.transitions):>5}%)")
        print(f"     5️⃣  Получили retention:        {row.got_retention:>6}  ({calculate_conversion(row.got_retention, row.transitions):>5}%)")
        print(f"     6️⃣  Купили подписку:           {row.bought_subscription:>6}  ({calculate_conversion(row.bought_subscription, row.transitions):>5}%)")

        print(f"\n  🎯 КЛЮЧЕВЫЕ МЕТРИКИ:")
        cr_quiz = calculate_conversion(row.completed_quiz, row.transitions)
        cr_gift = calculate_conversion(row.activated_gift, row.transitions)
        cr_purchase = calculate_conversion(row.bought_subscription, row.transitions)

        print(f"     • CR (переход → завершение квиза):  {cr_quiz}%")
        print(f"     • CR (переход → активация подарка): {cr_gift}%")
        print(f"     • CR (переход → покупка):           {cr_purchase}%  {'🔥' if cr_purchase > 20 else '⚠️' if cr_purchase > 10 else '❌'}")

        # Рассчитать среднюю стоимость привлечения если известен CPL
        if row.transitions > 0:
            print(f"\n  💸 ЭКОНОМИКА (при CPL = 100₽):")
            cpl = 100  # Стоимость за лид
            total_cost = row.transitions * cpl
            cpa = total_cost / row.bought_subscription if row.bought_subscription > 0 else 0
            print(f"     • Потрачено на рекламу:  {total_cost:>8}₽")
            print(f"     • CPA (стоимость покупки): {cpa:>8.0f}₽")

            # ROI если известна стоимость подписки
            subscription_price = 500  # средняя цена подписки
            revenue = row.bought_subscription * subscription_price
            roi = ((revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
            print(f"     • Выручка (500₽/подписка): {revenue:>8}₽")
            print(f"     • ROI:                     {roi:>8.0f}%  {'🚀' if roi > 100 else '✅' if roi > 0 else '❌'}")

    # Итоговая статистика
    print(f"\n\n{'='*100}")
    print("📊 ИТОГО ПО ВСЕМ ВОРОНКАМ")
    print(f"{'='*100}")

    total_transitions = sum(r.transitions for r in stats)
    total_quiz = sum(r.completed_quiz for r in stats)
    total_gift = sum(r.activated_gift for r in stats)
    total_purchase = sum(r.bought_subscription for r in stats)

    print(f"  Всего переходов:          {total_transitions}")
    print(f"  Завершили квиз:           {total_quiz} ({calculate_conversion(total_quiz, total_transitions)}%)")
    print(f"  Активировали подарок:     {total_gift} ({calculate_conversion(total_gift, total_transitions)}%)")
    print(f"  Купили подписку:          {total_purchase} ({calculate_conversion(total_purchase, total_transitions)}%)")

    print(f"\n{'='*100}\n")


async def main():
    """Главная функция"""
    try:
        stats = await get_funnel_stats()

        if not stats:
            print("\n⚠️  Нет данных по воронкам. Убедитесь, что пользователи переходили по рекламным ссылкам.")
            return

        print_funnel_report(stats)

    except Exception as e:
        print(f"\n❌ Ошибка при генерации отчета: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
