import type { ComandoDto } from '../dto/comandos.dto';
import type { Comando } from '../entities';

export function toComando(dto: ComandoDto): Comando {
  return {
    id: dto.id,
    etiqueta: dto.etiqueta,
    icono: dto.icono,
    argumentos: dto.argumentos,
    ejemplo: dto.ejemplo,
    ayuda: dto.ayuda,
    confirmar: dto.confirmar,
    sugiereTrabajador: dto.sugiere_trabajador,
    alias: dto.alias,
  };
}
