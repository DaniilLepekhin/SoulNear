rom datetime import datetime, timedelta
from sqlalchemy import insert, select
from database.models import Session, User, Media


def add_user_if_not_exists(user_id):
    with Session() as session:
        # Проверяем, существует ли пользователь
        result = session.execute(select(User).filter(User.user_id == user_id))
        user = result.scalars().first()

        if user:
            # Если пользователь существует, возвращаем его
            print("Пользователь найден в базе данных.")
            return user
        else:
            # Если пользователь не существует, создаем нового
            new_user = User(user_id=user_id)
            session.add(new_user)
            session.commit()  # Сохраняем изменения
            print("Новый пользователь добавлен в базу данных.")
            return new_user


def subscription_status(user_id: int):
    with Session() as session:
        # Получаем пользователя по user_id
        user = session.get(User, user_id)
        # Отслеживание срока подписки, присваивание статуса подписки и возвращение его для проверки в файле ChatGPT.py
        if user:
            # При добавлении пользователя у него нет периода подписки. Активируем ему пробный период на 14 дней
            if user.subscription_end_date == None:
                user.subscription_end_date = datetime.now() + timedelta(days=14)
                session.commit()
                subscription_status = 'trial'
                print(f"Статус подписки {subscription_status}")
                return subscription_status
            # Вышел срок подписки
            elif user.subscription_end_date <= datetime.now():
                subscription_status = 'inactive'
                print(f"Статус подписки {subscription_status}")
                return subscription_status
            # Подписка активна
            elif user.subscription_end_date > datetime.now():
                subscription_status = 'active'
                print(f"Статус подписки {subscription_status}")
                return subscription_status


def load_user_state(user_id: int):
    with Session() as session:
        result = session.execute(select(User).filter_by(user_id=user_id))
        user = result.scalars().first()
        if user:
            return user
        return None


def save_user_state(user_id: int, thread_id: str):
    with Session() as session:
        user = load_user_state(user_id)
        if user:
            user.thread = thread_id
            session.add(user)
            session.commit()


def add_media(file_id):
    with Session() as session:
        result = session.execute(select(Media).filter(Media.file_id == file_id))
        media = result.scalars().first()

        if media:
            print("Медиа уже добавлено в базу данных")
            return media
        else:
            new_media = Media(file_id=file_id)
            session.add(new_media)
            session.commit()
            return new_media
