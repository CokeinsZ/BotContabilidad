from mobile.controllers.auth_controller import create_auth_router
from mobile.controllers.chat_controller import create_chat_router
from mobile.controllers.commands_controller import create_commands_router
from mobile.controllers.planillas_controller import create_planillas_router
from mobile.controllers.profile_controller import create_profile_router
from mobile.controllers.workers_controller import create_workers_router

__all__ = [
    "create_auth_router",
    "create_chat_router",
    "create_commands_router",
    "create_planillas_router",
    "create_profile_router",
    "create_workers_router",
]
