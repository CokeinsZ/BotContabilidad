import type { PerfilDto } from '../dto/perfil.dto';
import type { Perfil } from '../entities';

export function toPerfil(dto: PerfilDto): Perfil {
  return {
    administrador: { ...dto.administrador },
    negocio: {
      id: dto.negocio.id,
      nombre: dto.negocio.nombre,
      carpetaPlanillasUrl: dto.negocio.carpeta_planillas_url,
      carpetaTrabajadoresUrl: dto.negocio.carpeta_trabajadores_url,
    },
    administradores: dto.administradores.map((companero) => ({
      id: companero.id,
      nombre: companero.nombre,
      esUsted: companero.es_usted,
    })),
    hoy: dto.hoy,
    googleConectado: dto.google_conectado,
    whatsappBot: dto.whatsapp_bot,
  };
}
