from sqlalchemy import Boolean, Date, DateTime, Integer, Float, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class AdminIds(Base):
    __tablename__ = 'admin_ids'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(Integer)


class AdminMenu(Base):
    __tablename__ = 'admin_menu_ids'

    id_note: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(Integer)
    inline_message_id: Mapped[str] = mapped_column(String(150))


class ClientMenu(Base):
    __tablename__ = 'client_menu_ids'

    id_note: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(Integer)
    inline_message_id: Mapped[str] = mapped_column(String(150))



class Car(Base):
    __tablename__ = 'cars'

    id_car: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_client: Mapped[int] = mapped_column(Integer, nullable=False)
    car_model: Mapped[str] = mapped_column(String(150), nullable=False)
    car_plate: Mapped[str] = mapped_column(String(150), nullable=True)
    car_vin: Mapped[str] = mapped_column(String(150), nullable=True)
    car_status: Mapped[bool] = mapped_column(Boolean, nullable=True)


class Client(Base):
    __tablename__ = 'clients'

    id_client: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone_client: Mapped[str] = mapped_column(String(150), nullable=True)
    id_telegram: Mapped[int] = mapped_column(Integer, nullable=True)
    nickname: Mapped[str] = mapped_column(String(150), nullable=True)


class ClientRequest(Base):
    __tablename__ = 'client_requests'

    id_request: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_telegram: Mapped[int] = mapped_column(Integer, nullable=False)
    date_message: Mapped[str] = mapped_column(Text)
    time_start: Mapped[str] = mapped_column(Text)
    text_request: Mapped[str] = mapped_column(Text)


class Notice(Base):
    __tablename__ = 'notices'


    id_notice: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[bool] = mapped_column(Boolean, nullable=True)
    id_telegram: Mapped[int] = mapped_column(Integer, nullable=True)
    id_order: Mapped[str] = mapped_column(Text, nullable=True)
    datetime_order: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    datetime_notice: Mapped[DateTime] = mapped_column(DateTime, nullable=True)


class Order(Base):
    __tablename__ = 'orders'

    id_order: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    begins: Mapped[DateTime] = mapped_column(DateTime)
    ends: Mapped[DateTime] = mapped_column(DateTime)
    place: Mapped[int] = mapped_column(Integer, nullable=True)
    id_car: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    longterm: Mapped[bool] = mapped_column(Boolean, nullable=True)
    mileage: Mapped[str] = mapped_column(String(150), nullable=True)
    advice: Mapped[str] = mapped_column(Text, nullable=True)
    grm: Mapped[bool] = mapped_column(Boolean, nullable=True)
    oil_m: Mapped[bool] = mapped_column(Boolean, nullable=True)
    oil_kpp: Mapped[bool] = mapped_column(Boolean, nullable=True)
    power_steer: Mapped[bool] = mapped_column(Boolean, nullable=True)
    fuel_filter: Mapped[bool] = mapped_column(Boolean, nullable=True)
    coolant: Mapped[bool] = mapped_column(Boolean, nullable=True)
    break_fluid: Mapped[bool] = mapped_column(Boolean, nullable=True)
    spark_plugs: Mapped[bool] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(String(150), nullable=True)
    sum: Mapped[int] = mapped_column(Integer, nullable=True)
    photo: Mapped[str] = mapped_column(Text, nullable=True)
    repair_photo: Mapped[str] = mapped_column(Text, nullable=True)
    id_client: Mapped[int] = mapped_column(Integer, nullable=True)
    create_date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    by_admin: Mapped[bool] = mapped_column(Boolean, nullable=True)