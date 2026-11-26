"""Armado de la API de la app móvil (`/app`).

`create_mobile_api` construye los servicios (lo llama el composition root,
`main.py`) e `install_mobile_api` los publica en la aplicación FastAPI junto
con el formato de errores `{"detail": ..., "codigo": ...}`.
"""
from dataclasses import dataclass
from typing import Callable

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from accounting.accounting_service import AccountingService
from accounting.dispatcher import CommandDispatcher
from config.clock import today_str
from database.business_repository import BusinessRepository
from drive.drive_client import DriveClient
from mobile.auth import AppAuthService
from mobile.cache import TtlCache
from mobile.chat import ChatService, CommandBuilder
from mobile.chat.command_builder import ExtractCommands
from mobile.controllers import (
    create_auth_router,
    create_chat_router,
    create_commands_router,
    create_planillas_router,
    create_profile_router,
    create_workers_router,
)
from mobile.errors import AppError
from mobile.google_gate import GoogleGate
from mobile.locks import KeyedLocks
from mobile.ownership import Ownership
from mobile.planillas_service import PlanillasService
from mobile.profile_service import ProfileService
from mobile.security import SlidingWindowLimiter
from mobile.security.dependencies import create_current_context, create_enabled_guard
from mobile.workers_service import WorkersService
from sheets.sheets_client import SheetsClient

PREFIX = "/app"
#: Cuánto se recuerdan los listados de Drive y los totales leídos de Sheets.
LISTINGS_TTL_SECONDS = 30


@dataclass
class MobileApi:
    auth: AppAuthService
    profiles: ProfileService
    planillas: PlanillasService
    chat: ChatService
    workers: WorkersService
    dispatcher: CommandDispatcher
    pairing_limiter: SlidingWindowLimiter


def create_mobile_api(
    *,
    auth: AppAuthService,
    accounting: AccountingService,
    dispatcher: CommandDispatcher,
    businesses: BusinessRepository,
    sheets: SheetsClient,
    drive: DriveClient,
    extract_commands: ExtractCommands,
    bot_whatsapp_number: str = "",
    pairings_per_ip: int = 10,
    today: Callable[[], str] = today_str,
) -> MobileApi:
    google = GoogleGate(sheets, drive)
    ownership = Ownership(drive)
    locks = KeyedLocks()
    listings = TtlCache(ttl_seconds=LISTINGS_TTL_SECONDS, max_items=2000)
    return MobileApi(
        auth=auth,
        profiles=ProfileService(businesses, google, bot_whatsapp_number, today=today),
        planillas=PlanillasService(accounting, drive, sheets, ownership, google, locks, listings, today=today),
        chat=ChatService(
            accounting, dispatcher, CommandBuilder(dispatcher, extract_commands),
            ownership, google, locks, listings,
        ),
        workers=WorkersService(drive, sheets, ownership, google, listings),
        dispatcher=dispatcher,
        pairing_limiter=SlidingWindowLimiter(max_events=pairings_per_ip, window_seconds=600),
    )


def create_mobile_router(api: MobileApi) -> APIRouter:
    router = APIRouter(prefix=PREFIX, dependencies=[Depends(create_enabled_guard(api.auth))])
    current = create_current_context(api.auth)
    router.include_router(create_auth_router(api.auth, api.profiles, api.pairing_limiter))
    router.include_router(create_profile_router(api.profiles, current))
    router.include_router(create_commands_router(api.dispatcher, current))
    router.include_router(create_planillas_router(api.planillas, current))
    router.include_router(create_chat_router(api.chat, current))
    router.include_router(create_workers_router(api.workers, current))
    return router


async def _app_error_handler(_request: Request, error: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
    return JSONResponse(
        status_code=error.status,
        content={"detail": error.message, "codigo": error.code},
        headers=headers,
    )


async def _validation_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    """En /app los datos inválidos se responden con el mismo formato que los demás errores."""
    if not request.url.path.startswith(PREFIX + "/"):
        return await request_validation_exception_handler(request, error)
    problems = []
    for item in error.errors():
        field = ".".join(str(part) for part in item.get("loc", ()) if part not in ("body", "query", "path"))
        problems.append(f"{field}: {item.get('msg')}" if field else str(item.get("msg")))
    return JSONResponse(
        status_code=422,
        content={"detail": "Datos inválidos: " + "; ".join(problems), "codigo": "DATOS_INVALIDOS"},
    )


def install_mobile_api(app: FastAPI, api: MobileApi) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.include_router(create_mobile_router(api))
