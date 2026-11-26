"""Catálogo de comandos para la banda del chat y la pantalla de Ayuda."""
from fastapi import APIRouter, Depends

from accounting.dispatcher import CommandDispatcher
from mobile.catalog import CATALOG, aliases_of
from mobile.dto import ComandoOut, comando_out
from mobile.security.dependencies import CurrentContext


def create_commands_router(dispatcher: CommandDispatcher, current: CurrentContext) -> APIRouter:
    router = APIRouter(tags=["App · Comandos"])
    commands = [comando_out(entry, aliases_of(dispatcher, entry)) for entry in CATALOG]

    @router.get("/comandos", response_model=list[ComandoOut], dependencies=[Depends(current)])
    async def list_commands():
        return commands

    return router
