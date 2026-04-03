from sqlalchemy import create_engine, Column, Integer, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from aiogram.types import User as AiogramUser


DATABASE_URL = "sqlite:///./base.db"
engine = create_engine(DATABASE_URL)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    ball = Column(Integer)


class RequiredJoins(Base):
    __tablename__ = "required_joins"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer)
    link = Column(Text)


class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    msg1 = Column(Text)
    msg2 = Column(Text)
    max_add_count = Column(Integer)
    main_chat = Column(Integer)
    main_chat_url = Column(Text)
    photo_message_id = Column(Integer, default=4771)


Base.metadata.create_all(bind=engine)

# Migration: add main_chat_url column if it doesn't exist
with engine.connect() as conn:
    cols = [row[1] for row in conn.execute(text("PRAGMA table_info(settings)"))]
    if 'main_chat_url' not in cols:
        conn.execute(text("ALTER TABLE settings ADD COLUMN main_chat_url TEXT"))
        conn.commit()

# Migration: add photo_message_id column if it doesn't exist
with engine.connect() as conn:
    cols = [row[1] for row in conn.execute(text("PRAGMA table_info(settings)"))]
    if 'photo_message_id' not in cols:
        conn.execute(text("ALTER TABLE settings ADD COLUMN photo_message_id INTEGER DEFAULT 4771"))
        conn.commit()

Session = sessionmaker(bind=engine)


class DataBase:
    def __init__(self):
        self.add_settings('text', 'text', 10, 0)
        self.bot : AiogramUser = None

    @staticmethod
    def add_user(user_id):
        with Session() as session:
            isuser = session.query(User).filter(User.user_id == user_id).first()

            if not isuser:
                user = User(user_id=user_id, ball=0)
                session.add(user)
                session.commit()
                return True
            return False

    @staticmethod
    def get_all_users():
        with Session() as session:
            users = session.query(User).all()
            return users

    @staticmethod
    def update_ball(user_id):
        with Session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.ball = user.ball + 1
                session.commit()
                return user.ball

    @staticmethod
    def get_ball(user_id):
        with Session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                return user.ball
            return 0

    @staticmethod
    def add_required_joins(chat_id, link):
        with Session() as session:
            required_joins = RequiredJoins(chat_id=chat_id, link=link)
            session.add(required_joins)
            session.commit()
            return required_joins

    @staticmethod
    def get_required_joins():
        with Session() as session:
            return session.query(RequiredJoins).all()

    @staticmethod
    def add_settings(msg1, msg2, max_add_count, main_chat_id):
        with Session() as session:
            issettings = session.query(Settings).all()
            if not issettings:
                settings = Settings(msg1=msg1, msg2=msg2, max_add_count=max_add_count, main_chat=main_chat_id, photo_message_id=4771)
                session.add(settings)
                session.commit()
                return settings

    @staticmethod
    def delete_required_joins(chat_id):
        with Session() as session:
            required_joins = session.query(RequiredJoins).filter(RequiredJoins.chat_id == chat_id).first()
            if required_joins:
                session.delete(required_joins)
                session.commit()
            return required_joins

    @staticmethod
    def edit_settings(method, new):
        with Session() as session:
            settings = session.query(Settings).first()
            if not settings:
                return None

            if method in ['msg1', 'msg2', 'max_add_count', 'main_chat', 'main_chat_url', 'photo_message_id']:
                setattr(settings, method, new)
                session.commit()
            return settings

    @staticmethod
    def get_settings():
        with Session() as session:
            res = session.query(Settings).first()
            return res


