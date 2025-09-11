import os
import asyncio
import logging
from aiogram import Bot
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select, Column, Integer, String, DateTime, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv

load_dotenv()


POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
DB_HOST = os.getenv('DB_HOST')

DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:5432/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BASE_MEDIA_PATH = 'E:/Telegram bots/SoulnearBot'
MY_ID = 946195257

#logging.basicConfig(format=u'%(filename)s [ LINE:%(lineno)+3s ]#%(levelname)+8s [%(asctime)s]  %(message)s',
                    #level=logging.DEBUG)

bot = Bot(os.getenv('BOT_TOKEN'))
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    #user_name = Column(Text, nullable=True)
    #user_email = Column(Text, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)
    thread = Column()


class Media(Base):
    __tablename__ = 'media'

    id = Column(Integer, primary_key=True)
    file_id = Column(String(255))
    filename = Column(String(255))


def create_tables():
    Base.metadata.create_all(bind=engine)


create_tables()


'''async def uploadMediaFiles(folder, method, file_attr):
    folder_path = os.path.join(BASE_MEDIA_PATH, folder)
    for filename in os.listdir(folder_path):
        if filename.startswith('.'):
            continue

        logging.info(f'Started processing {filename}')
        with open(os.path.join(folder_path, filename), 'rb') as file:
            msg = await method(MY_ID, file, disable_notification=True)
            if file_attr == 'photo':
                file_id = msg.photo[-1].file_id
            else:
                file_id = getattr(msg, file_attr).file_id
            session = Session()
            newItem = Media(file_id=file_id, filename=filename)
            try:
                session.add(newItem)
                session.commit()
            except Exception as e:
                logging.error(
                    'Couldn\'t upload {}. Error is {}'.format(filename, e))
            else:
                logging.info(
                    f'Successfully uploaded and saved to DB file {filename} with id {file_id}')
            finally:
                session.close()

loop = asyncio.get_event_loop()

tasks = [
    loop.create_task(uploadMediaFiles('yoga_1.MOV', bot.send_video, 'video')),
    loop.create_task(uploadMediaFiles('yoga_2.MOV', bot.send_video, 'video')),
    #loop.create_task(uploadMediaFiles('videoNotes', bot.send_video_note, 'video_note')),
    #loop.create_task(uploadMediaFiles('files', bot.send_document, 'document')),
    #loop.create_task(uploadMediaFiles('ogg', bot.send_voice, 'voice')),
]

wait_tasks = asyncio.wait(tasks)

loop.run_until_complete(wait_tasks)
loop.close()


select_stmt = select(Media)
conn = engine.connect()
result = conn.execute(select_stmt)
for row in result:
    print(row)
conn.close()

'''

