
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Backend.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    foto_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    identidades: Mapped[list["Identidade"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
    )


class Identidade(Base):
    __tablename__ = "identidades"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provedor: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="identidades")

    __table_args__ = (
        UniqueConstraint(
            "provedor",
            "provider_user_id",
            name="uq_identidade_provedor_usuario",
        ),
    )