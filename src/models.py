"""
models.py
---------
Definición del modelo ORM (SQLAlchemy) para la tabla `leads`.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    create_engine,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, Session

Base = declarative_base()


class Lead(Base):
    """Representa una empresa extraída del scraping."""

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    web = Column(String(512), nullable=True)
    nif = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    fuente = Column(String(100), nullable=True)
    keyword = Column(String(100), nullable=True)
    fecha_scraping = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Campos de subvenciones
    total_subvenciones = Column(Float, default=0.0, nullable=True)
    num_concesiones = Column(Integer, default=0, nullable=True)
    es_prioritario = Column(Boolean, default=False, nullable=True)
    
    # Campo de seguimiento comercial
    contactado = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("nombre", "fuente", name="uq_nombre_fuente"),
    )

    def __repr__(self) -> str:
        return (
            f"<Lead id={self.id} nombre='{self.nombre}' "
            f"web='{self.web}' email='{self.email}' contactado={self.contactado}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "web": self.web,
            "nif": self.nif,
            "email": self.email,
            "fuente": self.fuente,
            "keyword": self.keyword,
            "fecha_scraping": (
                self.fecha_scraping.isoformat() if self.fecha_scraping else None
            ),
            "total_subvenciones": self.total_subvenciones,
            "num_concesiones": self.num_concesiones,
            "es_prioritario": self.es_prioritario,
            "contactado": self.contactado,
        }


def init_db(database_url: str) -> Session:
    """
    Inicializa la base de datos SQLite y devuelve una sesión activa.

    Args:
        database_url: URL de conexión SQLAlchemy (ej: 'sqlite:///data/leads.db')

    Returns:
        Sesión SQLAlchemy lista para usar.
    """
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return Session(engine)
