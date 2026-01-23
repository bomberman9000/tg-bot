from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Boolean, Text, Integer, Float, Enum
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
import enum

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_carrier: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CargoStatus(enum.Enum):
    NEW = "new"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Cargo(Base):
    __tablename__ = "cargos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger)  # кто создал
    carrier_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # кто взял
    
    # Маршрут
    from_city: Mapped[str] = mapped_column(String(100))
    to_city: Mapped[str] = mapped_column(String(100))
    
    # Груз
    cargo_type: Mapped[str] = mapped_column(String(100))
    weight: Mapped[float] = mapped_column(Float)  # тонны
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)  # м³
    
    # Условия
    price: Mapped[int] = mapped_column(Integer)  # рубли
    load_date: Mapped[datetime] = mapped_column(DateTime)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status: Mapped[CargoStatus] = mapped_column(Enum(CargoStatus), default=CargoStatus.NEW)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CargoResponse(Base):
    __tablename__ = "cargo_responses"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    cargo_id: Mapped[int] = mapped_column(Integer)
    carrier_id: Mapped[int] = mapped_column(BigInteger)
    price_offer: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedback"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Reminder(Base):
    __tablename__ = "reminders"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[str] = mapped_column(Text)
    remind_at: Mapped[datetime] = mapped_column(DateTime)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
