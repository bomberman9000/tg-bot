from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Boolean, Text, Integer, Float, Enum, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
import enum

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_carrier: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    trust_score: Mapped[int] = mapped_column(Integer, default=50)
    warnings_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class UserRole(enum.Enum):
    CUSTOMER = "customer"
    CARRIER = "carrier"
    FORWARDER = "forwarder"

class VerificationStatus(enum.Enum):
    BASIC = "basic"
    CONFIRMED = "confirmed"
    VERIFIED = "verified"

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER)
    inn: Mapped[str | None] = mapped_column(String(12), nullable=True)
    ogrn: Mapped[str | None] = mapped_column(String(15), nullable=True)
    director_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.BASIC
    )
    verification_doc_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CargoStatus(enum.Enum):
    NEW = "new"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class Cargo(Base):
    __tablename__ = "cargos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger)
    carrier_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    client_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    forwarder_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    from_city: Mapped[str] = mapped_column(String(100))
    to_city: Mapped[str] = mapped_column(String(100))
    
    cargo_type: Mapped[str] = mapped_column(String(100))
    weight: Mapped[float] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    price: Mapped[int] = mapped_column(Integer)
    actual_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    load_date: Mapped[datetime] = mapped_column(DateTime)
    load_time: Mapped[str | None] = mapped_column(String(10), nullable=True)  # формат "HH:MM"
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status: Mapped[CargoStatus] = mapped_column(Enum(CargoStatus), default=CargoStatus.NEW)
    tracking_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(Integer, ForeignKey("cargos.id"))
    type: Mapped[str] = mapped_column(String(1))  # "A" или "B"
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, sent, signed, cancelled

    created_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    selected_carrier_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Подписи
    signed_by_client_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    signed_by_forwarder_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    signed_by_carrier_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Рендер
    rendered_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rendered_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # PDF
    pdf_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pdf_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ApplicationPartySnapshot(Base):
    __tablename__ = "application_party_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("applications.id"))
    role: Mapped[str] = mapped_column(String(20))  # client, forwarder, carrier
    payload_json: Mapped[str] = mapped_column(Text)  # JSON с реквизитами
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CompanyDetails(Base):
    __tablename__ = "company_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True)

    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inn: Mapped[str | None] = mapped_column(String(12), nullable=True)
    kpp: Mapped[str | None] = mapped_column(String(9), nullable=True)
    ogrn: Mapped[str | None] = mapped_column(String(15), nullable=True)
    legal_address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_bik: Mapped[str | None] = mapped_column(String(9), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_corr_account: Mapped[str | None] = mapped_column(String(20), nullable=True)

    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(100), nullable=True)

    driver_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    driver_passport: Mapped[str | None] = mapped_column(String(100), nullable=True)
    driver_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vehicle_info: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Рейтинг (10-балльная система)
    rating_registration: Mapped[int] = mapped_column(Integer, default=2)  # ИП/ООО = 2, физлицо = 0
    rating_subscription: Mapped[int] = mapped_column(Integer, default=0)  # подписка = +1
    rating_experience: Mapped[int] = mapped_column(Integer, default=0)    # >1 года = +1
    rating_verified: Mapped[int] = mapped_column(Integer, default=0)      # верификация = +1
    rating_deals_completed: Mapped[int] = mapped_column(Integer, default=0)  # 10+ сделок = +1, 50+ = +2
    rating_no_claims: Mapped[int] = mapped_column(Integer, default=1)     # нет претензий = +1, есть = -1
    rating_response_time: Mapped[int] = mapped_column(Integer, default=0)  # быстрый ответ = +1
    rating_documents: Mapped[int] = mapped_column(Integer, default=0)      # документы в порядке = +1

    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def total_rating(self) -> int:
        """Вычисляемый общий рейтинг (сумма, макс 10)."""
        total = (
            self.rating_registration
            + self.rating_subscription
            + self.rating_experience
            + self.rating_verified
            + self.rating_deals_completed
            + self.rating_no_claims
            + self.rating_response_time
            + self.rating_documents
        )
        return min(10, max(0, total))


class ClaimStatus(enum.Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Кто подаёт
    from_user_id: Mapped[int] = mapped_column(BigInteger)
    from_company_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("company_details.id"), nullable=True)

    # На кого подаёт
    to_user_id: Mapped[int] = mapped_column(BigInteger)
    to_company_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("company_details.id"), nullable=True)

    # Связь со сделкой (опционально)
    cargo_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("cargos.id"), nullable=True)

    # Данные претензии
    claim_type: Mapped[str] = mapped_column(String(50))  # payment, damage, delay, fraud, other
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)  # сумма претензии в рублях

    # Статус
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), default=ClaimStatus.OPEN)

    # Ответ компании
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Решение (админ)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(20))
    entity_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(30))
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)
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

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_city: Mapped[str] = mapped_column(String(100))
    to_city: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column()  # цена за 20 тонн без НДС
    cargo_type: Mapped[str] = mapped_column(String(50), default="тент")  # тент, реф, изотерм
    weight: Mapped[float] = mapped_column(default=20.0)  # базовый вес
    source: Mapped[str] = mapped_column(String(100), default="umnayalogistika")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_market_route", "from_city", "to_city", "cargo_type", unique=True),
    )

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

class RouteSubscription(Base):
    __tablename__ = "route_subscriptions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    from_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    to_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Rating(Base):
    __tablename__ = "ratings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    cargo_id: Mapped[int] = mapped_column(Integer)
    from_user_id: Mapped[int] = mapped_column(BigInteger)
    to_user_id: Mapped[int] = mapped_column(BigInteger)
    score: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    cargo_id: Mapped[int] = mapped_column(Integer)
    from_user_id: Mapped[int] = mapped_column(BigInteger)
    to_user_id: Mapped[int] = mapped_column(BigInteger)
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ReportType(enum.Enum):
    FRAUD = "fraud"
    SPAM = "spam"
    FAKE_CARGO = "fake_cargo"
    NO_PAYMENT = "no_payment"
    OTHER = "other"

class Report(Base):
    __tablename__ = "reports"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    from_user_id: Mapped[int] = mapped_column(BigInteger)
    to_user_id: Mapped[int] = mapped_column(BigInteger)
    cargo_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType))
    description: Mapped[str] = mapped_column(Text)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CargoLocation(Base):
    __tablename__ = "cargo_locations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    cargo_id: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(BigInteger)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
