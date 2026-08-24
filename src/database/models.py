"""Modelos de dominio del módulo de persistencia."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Business:
    id: int
    name: str
    sheets_folder_id: str
    state: str


@dataclass(frozen=True)
class Administrator:
    id: int
    business_id: int
    name: str
    phone_number: str
    state: str


@dataclass(frozen=True)
class BusinessContext:
    """Business junto con el administrador que originó la petición."""

    business: Business
    administrator: Administrator
