from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(Text, unique=True)
    value: Mapped[str] = mapped_column(Text)

