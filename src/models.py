
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime as dt
from external_requests import GetWeatherRequest

Base = declarative_base()

class City(Base):
    """
    Город
    """
    __tablename__ = 'city'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    @property
    def weather(self) -> str:
        """
        Возвращает текущую погоду в этом городе
        """
        r = GetWeatherRequest()
        weather = r.get_weather(self.name)
        return weather

    def __repr__(self):
        return f'<Город "{self.name}">'


class User(Base):
    """
    Пользователь
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    age = Column(Integer, nullable=True)

    def __repr__(self):
        return f'<Пользователь {self.surname} {self.name}>'


class Picnic(Base):
    """
    Пикник
    """
    __tablename__ = 'picnic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(Integer, ForeignKey('city.id'), nullable=False)
    time = Column(DateTime, nullable=False)

    def __repr__(self):
        return f'<Пикник {self.id}>'


class PicnicRegistration(Base):
    """
    Регистрация пользователя на пикник
    """
    __tablename__ = 'picnic_registration'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    picnic_id = Column(Integer, ForeignKey('picnic.id'), nullable=False)

    user = relationship('User', backref='picnics')
    picnic = relationship('Picnic', backref='users')

    def __repr__(self):
        return f'<Регистрация {self.id}>'

class RegisterUserRequest(BaseModel):
    name: str
    surname: str
    age: int


class UserModel(BaseModel):
    id: int
    name: str
    surname: str
    age: int

    class Config:
        orm_mode = True


class PicnicCreate(BaseModel):   #Новая модель
    city_id: int
    datetime: dt

class RegisterPicnicRequest(BaseModel):   #Новая модель
    user_id: int
    picnic_id: int


class CityCreate(BaseModel): #Новая модель
    name: str
