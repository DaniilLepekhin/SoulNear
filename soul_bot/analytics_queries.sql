-- 📊 АНАЛИТИКА КОНВЕРСИИ ПО ВОРОНКАМ
-- Используйте эти SQL запросы для отслеживания эффективности каждой рекламной ссылки
-- Как использовать: скопируйте запрос и выполните в PostgreSQL
-- docker exec -i soulnear_postgres psql -U postgres -d soul_bot < query.sql

-- ============================================================================
-- 1. 🔥 ГЛАВНАЯ СТАТИСТИКА ПО ВСЕМ ВОРОНКАМ (самый важный запрос!)
-- ============================================================================

SELECT
    raw_link as "Ссылка",
    COUNT(DISTINCT de.user_id) as "1️⃣ Переходов",
    COUNT(DISTINCT CASE WHEN qs.id IS NOT NULL THEN de.user_id END) as "2️⃣ Начали квиз",
    COUNT(DISTINCT CASE WHEN qs.status = 'completed' THEN de.user_id END) as "3️⃣ Завершили квиз",
    COUNT(DISTINCT CASE WHEN u.free_messages_activated = true THEN de.user_id END) as "4️⃣ Активировали подарок",
    COUNT(DISTINCT CASE WHEN u.last_retention_sent IS NOT NULL THEN de.user_id END) as "5️⃣ Получили retention",
    COUNT(DISTINCT CASE WHEN u.sub_date > NOW() THEN de.user_id END) as "6️⃣ Купили подписку",

    -- Конверсии в %
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN qs.status = 'completed' THEN de.user_id END) / NULLIF(COUNT(DISTINCT de.user_id), 0), 1) as "CR квиз %",
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN u.free_messages_activated = true THEN de.user_id END) / NULLIF(COUNT(DISTINCT de.user_id), 0), 1) as "CR подарок %",
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN u.sub_date > NOW() THEN de.user_id END) / NULLIF(COUNT(DISTINCT de.user_id), 0), 1) as "CR подписка %"
FROM
    deeplink_events de
LEFT JOIN
    quiz_sessions qs ON de.quiz_session_id = qs.id
LEFT JOIN
    users u ON de.user_id = u.user_id
WHERE
    de.raw_link IN ('analysis_relationships_ads', 'analysis_money_ads', 'analysis_purpose_ads')
GROUP BY
    de.raw_link
ORDER BY
    COUNT(DISTINCT de.user_id) DESC;


-- ============================================================================
-- 2. ДЕТАЛЬНАЯ ВОРОНКА ДЛЯ ОДНОЙ ССЫЛКИ (relationships)
-- ============================================================================

WITH funnel_data AS (
    SELECT
        de.user_id,
        de.created_at as transition_time,
        qs.created_at as quiz_start_time,
        qs.completed_at as quiz_complete_time,
        u.free_messages_offered,
        u.free_messages_activated,
        u.sub_date,
        CASE WHEN qs.id IS NOT NULL THEN 1 ELSE 0 END as started_quiz,
        CASE WHEN qs.status = 'completed' THEN 1 ELSE 0 END as completed_quiz,
        CASE WHEN u.free_messages_activated = true THEN 1 ELSE 0 END as activated_gift,
        CASE WHEN u.sub_date > NOW() THEN 1 ELSE 0 END as has_subscription
    FROM
        deeplink_events de
    LEFT JOIN
        quiz_sessions qs ON de.quiz_session_id = qs.id
    LEFT JOIN
        users u ON de.user_id = u.user_id
    WHERE
        de.raw_link = 'analysis_relationships_ads'
)
SELECT
    'Этап 1: Переход по ссылке' as stage,
    COUNT(DISTINCT user_id) as users,
    100.0 as conversion_percent,
    '' as notes
FROM funnel_data
UNION ALL
SELECT
    'Этап 2: Начало квиза' as stage,
    SUM(started_quiz) as users,
    ROUND(100.0 * SUM(started_quiz) / NULLIF(COUNT(*), 0), 2) as conversion_percent,
    'От переходов' as notes
FROM funnel_data
UNION ALL
SELECT
    'Этап 3: Завершение квиза' as stage,
    SUM(completed_quiz) as users,
    ROUND(100.0 * SUM(completed_quiz) / NULLIF(COUNT(*), 0), 2) as conversion_percent,
    'От переходов' as notes
FROM funnel_data
UNION ALL
SELECT
    'Этап 4: Активация подарка' as stage,
    SUM(activated_gift) as users,
    ROUND(100.0 * SUM(activated_gift) / NULLIF(COUNT(*), 0), 2) as conversion_percent,
    'От переходов' as notes
FROM funnel_data
UNION ALL
SELECT
    'Этап 5: Покупка подписки' as stage,
    SUM(has_subscription) as users,
    ROUND(100.0 * SUM(has_subscription) / NULLIF(COUNT(*), 0), 2) as conversion_percent,
    'От переходов' as notes
FROM funnel_data;


-- ============================================================================
-- 3. СРАВНЕНИЕ ВОРОНОК ПО ДНЯМ
-- ============================================================================

SELECT
    DATE(de.created_at) as date,
    de.raw_link,
    COUNT(DISTINCT de.user_id) as transitions,
    COUNT(DISTINCT CASE WHEN qs.status = 'completed' THEN de.user_id END) as completed_quiz,
    COUNT(DISTINCT CASE WHEN u.free_messages_activated = true THEN de.user_id END) as activated_gift,
    COUNT(DISTINCT CASE WHEN u.sub_date > NOW() THEN de.user_id END) as subscriptions
FROM
    deeplink_events de
LEFT JOIN
    quiz_sessions qs ON de.quiz_session_id = qs.id
LEFT JOIN
    users u ON de.user_id = u.user_id
WHERE
    de.raw_link IN ('analysis_relationships_ads', 'analysis_money_ads', 'analysis_purpose_ads')
    AND de.created_at >= NOW() - INTERVAL '30 days'
GROUP BY
    DATE(de.created_at), de.raw_link
ORDER BY
    date DESC, de.raw_link;


-- ============================================================================
-- 4. ВРЕМЯ ДО КОНВЕРСИИ (как быстро пользователи покупают после прохождения квиза)
-- ============================================================================

SELECT
    de.raw_link as funnel,
    ROUND(AVG(EXTRACT(EPOCH FROM (u.reg_date - de.created_at)) / 3600), 2) as "Часов до подписки (среднее)",
    MIN(EXTRACT(EPOCH FROM (u.reg_date - de.created_at)) / 3600) as "Минимум часов",
    MAX(EXTRACT(EPOCH FROM (u.reg_date - de.created_at)) / 3600) as "Максимум часов"
FROM
    deeplink_events de
LEFT JOIN
    users u ON de.user_id = u.user_id
WHERE
    de.raw_link IN ('analysis_relationships_ads', 'analysis_money_ads', 'analysis_purpose_ads')
    AND u.sub_date > NOW()
GROUP BY
    de.raw_link;


-- ============================================================================
-- 5. RETENTION: Сколько пользователей получили retention сообщения после воронки
-- ============================================================================

SELECT
    de.raw_link as funnel,
    COUNT(DISTINCT u.user_id) as "Всего пользователей",
    COUNT(DISTINCT CASE WHEN u.last_retention_sent IS NOT NULL THEN u.user_id END) as "Получили retention",
    COUNT(DISTINCT CASE WHEN u.last_retention_message > 0 THEN u.user_id END) as "Получили хотя бы 1 сообщение",
    ROUND(AVG(u.last_retention_message), 2) as "Среднее кол-во retention сообщений"
FROM
    deeplink_events de
LEFT JOIN
    users u ON de.user_id = u.user_id
WHERE
    de.raw_link IN ('analysis_relationships_ads', 'analysis_money_ads', 'analysis_purpose_ads')
    AND u.free_messages_activated = true
    AND u.sub_date < NOW()  -- Нет подписки
GROUP BY
    de.raw_link;


-- ============================================================================
-- 6. СПИСОК ПОЛЬЗОВАТЕЛЕЙ КОНКРЕТНОЙ ВОРОНКИ (для ручного анализа)
-- ============================================================================

SELECT
    de.user_id,
    u.name,
    u.username,
    de.created_at as "Переход по ссылке",
    qs.created_at as "Начало квиза",
    qs.completed_at as "Завершение квиза",
    CASE WHEN u.free_messages_activated THEN 'Да' ELSE 'Нет' END as "Активировал подарок",
    u.free_messages_count as "Осталось бесплатных сообщений",
    CASE WHEN u.sub_date > NOW() THEN 'Да' ELSE 'Нет' END as "Есть подписка",
    u.last_retention_message as "Получено retention сообщений"
FROM
    deeplink_events de
LEFT JOIN
    quiz_sessions qs ON de.quiz_session_id = qs.id
LEFT JOIN
    users u ON de.user_id = u.user_id
WHERE
    de.raw_link = 'analysis_relationships_ads'  -- Замени на нужную воронку
ORDER BY
    de.created_at DESC
LIMIT 100;


-- ============================================================================
-- 7. A/B ТЕСТ: Сравнение эффективности разных категорий
-- ============================================================================

SELECT
    resolved_category as "Категория",
    COUNT(DISTINCT de.user_id) as "Пользователей",
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN qs.status = 'completed' THEN de.user_id END) /
          NULLIF(COUNT(DISTINCT de.user_id), 0), 2) as "CR: Завершение квиза (%)",
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN u.sub_date > NOW() THEN de.user_id END) /
          NULLIF(COUNT(DISTINCT de.user_id), 0), 2) as "CR: Покупка (%)",
    -- LTV расчет (если знаем цену подписки)
    COUNT(DISTINCT CASE WHEN u.sub_date > NOW() THEN de.user_id END) * 500 as "LTV (₽, если подписка 500₽)"
FROM
    deeplink_events de
LEFT JOIN
    quiz_sessions qs ON de.quiz_session_id = qs.id
LEFT JOIN
    users u ON de.user_id = u.user_id
WHERE
    de.raw_link IN ('analysis_relationships_ads', 'analysis_money_ads', 'analysis_purpose_ads')
GROUP BY
    resolved_category
ORDER BY
    "CR: Покупка (%)" DESC;


-- ============================================================================
-- 8. КОГОРТНЫЙ АНАЛИЗ: Конверсия по неделям запуска
-- ============================================================================

SELECT
    DATE_TRUNC('week', de.created_at) as week_start,
    de.raw_link,
    COUNT(DISTINCT de.user_id) as users,
    COUNT(DISTINCT CASE WHEN u.sub_date > NOW() THEN de.user_id END) as subscribers,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN u.sub_date > NOW() THEN de.user_id END) /
          NULLIF(COUNT(DISTINCT de.user_id), 0), 2) as conversion_rate
FROM
    deeplink_events de
LEFT JOIN
    users u ON de.user_id = u.user_id
WHERE
    de.raw_link IN ('analysis_relationships_ads', 'analysis_money_ads', 'analysis_purpose_ads')
GROUP BY
    DATE_TRUNC('week', de.created_at), de.raw_link
ORDER BY
    week_start DESC, de.raw_link;
