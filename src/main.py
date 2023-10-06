import datetime as dt
import time
from decouple import config
from external_requests import CheckCityExisting
from models import RegisterUserRequest, UserModel, Base, City, User, Picnic, PicnicRegistration, PicnicCreate, \
    RegisterPicnicRequest, CityCreate
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, desc, asc
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, HTTPException, Query, Depends
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('app.log')

file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
#Ваши значения postgres в .env
SQLALCHEMY_DATABASE_URI = config('DATABASE_URL')
engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# работает http://127.0.0.1:8000/create-city/
@app.post('/create-city/', summary='Create City', description='Создание города по его названию', tags=['city'])
def create_city(city: CityCreate, db: Session = Depends(get_db)):
    """
    Добавление города в базу
    """
    if city is None:
        raise HTTPException(status_code=400, detail='Параметр city должен быть указан')

    check = CheckCityExisting()
    if not check.check_existing(city):
        raise HTTPException(status_code=400, detail='Параметр city должен быть существующим городом')

    city_object = db.query(City).filter(City.name == city.name.capitalize()).first()

    if city_object is None:
        city_object = City(name=city.name.capitalize())
        db.add(city_object)
        db.commit()
        logger.info(f'City "{city.name}" was successfully created')

    return {'id': city_object.id, 'name': city_object.name, 'weather': city_object.weather}


# Работает http://127.0.0.1:8000/get-cities/
# Работает http://127.0.0.1:8000/get-cities/?q=Kazan
@app.get('/get-cities/', summary='Get Cities', tags=['city'])  # Поменял на get
def cities_list(q: str = Query(description="Название города", default=None), db: Session = Depends(get_db)):
    """
    Получение списка городов
    """

    if q is not None:
        cities = db.query(City).filter(City.name == q).all()
    else:
        cities = db.query(City).all()

    logger.info(f'GET /get-cities/ List of cities received')
    return [{'id': city.id, 'name': city.name, 'weather': city.weather} for city in cities]


# Работает http://127.0.0.1:8000/users-list/
# Работает http://127.0.0.1:8000/users-list/?q=min

@app.get('/users-list/', summary='User List', tags=['user'])
def users_list(q: str = Query(description='Возраст max/min', default=None), db: Session = Depends(get_db)):
    """
    Список пользователей
    + сортировка по age
    """

    query = db.query(User)

    if q == 'max':
        users = query.order_by(desc(User.age)).all()
    elif q == 'min':
        users = query.order_by(asc(User.age)).all()
    else:
        users = query.all()

    logger.info(f'GET /user-list/ User list received')
    return [{
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'age': user.age,
    } for user in users]


# Работает http://127.0.0.1:8000/register-user/
# {
#     "name": "fdsdfs",
#     "surname": "dsfdfsdfs",
#     "age": 54
# }
# При ошибки 422 fastapi сам все пишет

@app.post('/register-user/', summary='CreateUser', response_model=dict, tags=['user'])
def register_user(user: RegisterUserRequest, db: Session = Depends(get_db)):
    """
    Регистрация пользователя
    """

    user_object = User(name=user.name, surname=user.surname, age=user.age)
    db.add(user_object)
    db.commit()
    user_id = user_object.id

    response_data = {
        "message": "Профиль успешно создан",
        "id": user_id,
        "name": user.name,
        "surname": user.surname,
        "age": user.age
    }
    logger.info(
        f'POST /register-user/ Users created id:{user_id},name:{user.name},surname:{user.surname},age:{user.age}')
    return response_data


# Работает http://127.0.0.1:8000/all-picnics/

@app.get('/all-picnics/', summary='All Picnics', tags=['picnic'])
def all_picnics(datetime: dt.datetime = Query(default=None, description='Время пикника (по умолчанию не задано)'),
                past: bool = Query(default=True, description='Включая уже прошедшие пикники'),
                db: Session = Depends(get_db)):
    """
    Список всех пикников
    """

    picnics = db.query(Picnic)
    if datetime is not None:
        picnics = picnics.filter(Picnic.time == datetime)
    if not past:
        picnics = picnics.filter(Picnic.time >= dt.datetime.now())

    logger.info(f'GET /all-picnics/ Picnic registration list')

    return [{
        'id': pic.id,
        'city': db.query(City).filter(City.id == pic.city_id).first().name,
        'time': pic.time,
        'users': [
            {
                'id': pr.user.id,
                'name': pr.user.name,
                'surname': pr.user.surname,
                'age': pr.user.age,
            }
            for pr in db.query(PicnicRegistration).filter(PicnicRegistration.picnic_id == pic.id)],
    } for pic in picnics]


# Работает http://127.0.0.1:8000/picnic-add/
# {
#     "city_id": 12,
#     "datetime": "2024-10-10T14:00:00"
# }

@app.post('/picnic-add/', summary='Picnic Add', response_model=dict, tags=['picnic'])  # Изменил на post
def picnic_add(p: PicnicCreate, db: Session = Depends(get_db)):
    """
    Создание пикника
    """
    new_picnic = Picnic(city_id=p.city_id, time=p.datetime)
    db.add(new_picnic)
    db.commit()
    city = db.query(City).filter(City.id == new_picnic.city_id).first()

    logger.info(f'POST /picnic-add/ Picnic created id:{new_picnic.id},city:{city.name},time:{new_picnic.time}')

    return {
        "message": "Пикник успешно создан",
        'id': new_picnic.id,
        'city': city.name,
        'time': new_picnic.time,
    }


# Работает http://127.0.0.1:8000/picnic-register/
# {
#     "user_id":
#     "picnic_id"
# }
@app.post('/picnic-register/', summary='Picnic Registration', tags=['picnic'])
def register_to_picnic(register_picnic: RegisterPicnicRequest, db: Session = Depends(get_db)):
    """
    Регистрация пользователя на пикник
    """

    user = db.query(User).filter(User.id == register_picnic.user_id).first()
    picnic = db.query(Picnic).filter(Picnic.id == register_picnic.picnic_id).first()

    if user is None or picnic is None:
        return {"message": "Пользователь или пикник не найден"}

    picnic_location = db.query(City).filter(City.id == picnic.city_id).first()

    registration_picnic = PicnicRegistration(user=user, picnic=picnic)

    db.add(registration_picnic)
    db.commit()

    registration_data = {
        "message": "Пользователь успешно зарегистрировался на пикник",
        "user_id": user.id,
        "user_name": user.name,
        "picnic_id": picnic.id,
        "picnic_location": picnic_location.name,
        'weather': picnic_location.weather,
    }

    return registration_data
