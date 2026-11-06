"""ClienteService — CRUD de clientes (módulo D)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.pedidos.clientes import Cliente
from app.repositories.pedidos import ClienteRepo


class ClienteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ClienteRepo(db)

    def crear(
        self,
        *,
        nombre: str,
        identificacion: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        notas: str | None = None,
        activo: bool = True,
    ) -> Cliente:
        cliente = Cliente(
            nombre=nombre.strip(),
            identificacion=identificacion,
            telefono=telefono,
            email=email,
            direccion=direccion,
            notas=notas,
            activo=activo,
        )
        self.repo.agregar(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente

    def listar(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[Cliente]:
        return self.repo.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> Cliente:
        return self.repo.obtener_o_404(id_, "cliente")

    def actualizar(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        identificacion: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        notas: str | None = None,
        activo: bool | None = None,
    ) -> Cliente:
        cliente = self.obtener(id_)
        if nombre is not None:
            cliente.nombre = nombre.strip()
        if identificacion is not None:
            cliente.identificacion = identificacion
        if telefono is not None:
            cliente.telefono = telefono
        if email is not None:
            cliente.email = email
        if direccion is not None:
            cliente.direccion = direccion
        if notas is not None:
            cliente.notas = notas
        if activo is not None:
            cliente.activo = activo
        self.db.commit()
        self.db.refresh(cliente)
        return cliente

    def eliminar(self, id_: int) -> None:
        """Baja lógica: marca activo=false (conserva historial de pedidos)."""
        cliente = self.obtener(id_)
        cliente.activo = False
        self.db.commit()
