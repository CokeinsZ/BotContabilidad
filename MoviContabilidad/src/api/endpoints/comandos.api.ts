/** GET /app/comandos: catálogo de la banda del chat. */
import { request } from '../client/http';
import type { ComandoDto } from '../dto/comandos.dto';
import type { Comando } from '../entities';
import { toComando } from '../mappers/comandos.mapper';

export async function listarComandos(): Promise<Comando[]> {
  return (await request<ComandoDto[]>('/comandos')).map(toComando);
}
