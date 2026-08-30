"""
Herramienta de línea de comandos para administrar businesses.

Uso (desde la raíz del proyecto):

    python src/cli.py add-business "Pan de Oro" <sheets_folder_id>
    python src/cli.py add-admin <business_id> "Dairo Carvajal" 573001234567
    python src/cli.py list-businesses
    python src/cli.py list-admins <business_id>
"""
import argparse

from config import get_settings
from database import BusinessRepository, Database


def normalize_phone(phone: str) -> str:
    """Deja solo los dígitos del número telefónico."""
    return "".join(filter(str.isdigit, phone))


def build_repository() -> BusinessRepository:
    settings = get_settings()
    database = Database(
        db_path=settings.database_path, schema_path=settings.database_schema_path
    )
    return BusinessRepository(database)


def cmd_add_business(args) -> None:
    repository = build_repository()
    business = repository.create_business(
        args.name, args.sheets_folder_id, args.workers_folder
    )
    print(f"✅ Business creado: id={business.id} name='{business.name}'")


def cmd_set_workers_folder(args) -> None:
    repository = build_repository()
    business = repository.find_by_id(args.business_id)
    if business is None:
        print(f"⚠️ No existe un business con id {args.business_id}.")
        return
    repository.update_workers_folder(args.business_id, args.workers_folder_id)
    print(f"✅ Carpeta de trabajadores de '{business.name}' actualizada: {args.workers_folder_id}")


def cmd_add_admin(args) -> None:
    repository = build_repository()
    business = repository.find_by_id(args.business_id)
    if business is None:
        print(f"⚠️ No existe un business con id {args.business_id}.")
        return
    admin = repository.create_administrator(
        business_id=args.business_id,
        name=args.name,
        phone_number=normalize_phone(args.phone),
    )
    print(
        f"✅ Administrador creado: id={admin.id} name='{admin.name}' "
        f"phone={admin.phone_number} business='{business.name}'"
    )


def cmd_list_businesses(_args) -> None:
    repository = build_repository()
    businesses = repository.list_all()
    if not businesses:
        print("No hay businesses registrados.")
        return
    for business in businesses:
        print(
            f"[{business.id}] {business.name} "
            f"(planillas: {business.sheets_folder_id}, "
            f"trabajadores: {business.workers_folder_id or 'sin configurar'}, "
            f"estado: {business.state})"
        )


def cmd_list_admins(args) -> None:
    repository = build_repository()
    admins = repository.list_administrators(args.business_id)
    if not admins:
        print("No hay administradores registrados para ese business.")
        return
    for admin in admins:
        print(f"[{admin.id}] {admin.name} - {admin.phone_number} ({admin.state})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Administración del Bot de Contabilidad")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_business = subparsers.add_parser("add-business", help="Registrar un business")
    add_business.add_argument("name", help="Nombre del negocio (se escribe en A2:E2 de cada planilla)")
    add_business.add_argument("sheets_folder_id", help="ID de la carpeta de Drive donde se guardan sus planillas")
    add_business.add_argument("--workers-folder", dest="workers_folder", default=None,
                              help="ID de la carpeta de Drive donde se guardan los archivos de trabajadores")
    add_business.set_defaults(func=cmd_add_business)

    set_workers = subparsers.add_parser("set-workers-folder", help="Configurar la carpeta de trabajadores de un business")
    set_workers.add_argument("business_id", type=int, help="ID del business")
    set_workers.add_argument("workers_folder_id", help="ID de la carpeta de Drive de trabajadores")
    set_workers.set_defaults(func=cmd_set_workers_folder)

    add_admin = subparsers.add_parser("add-admin", help="Registrar un administrador")
    add_admin.add_argument("business_id", type=int, help="ID del business")
    add_admin.add_argument("name", help="Nombre del administrador (se escribe en B6 de cada planilla)")
    add_admin.add_argument("phone", help="Número de WhatsApp del administrador")
    add_admin.set_defaults(func=cmd_add_admin)

    list_businesses = subparsers.add_parser("list-businesses", help="Listar businesses")
    list_businesses.set_defaults(func=cmd_list_businesses)

    list_admins = subparsers.add_parser("list-admins", help="Listar administradores de un business")
    list_admins.add_argument("business_id", type=int, help="ID del business")
    list_admins.set_defaults(func=cmd_list_admins)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
