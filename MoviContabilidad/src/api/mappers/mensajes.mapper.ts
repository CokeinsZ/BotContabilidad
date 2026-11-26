import type { EstadoChatDto, RespuestaDto, ResultadoChatDto, SeleccionDto } from '../dto/mensajes.dto';
import type { EstadoChat, RespuestaBot, ResultadoChat, Seleccion } from '../entities';

export function toRespuesta(dto: RespuestaDto): RespuestaBot {
  return { tipo: dto.tipo, texto: dto.texto };
}

function toSeleccion(dto: SeleccionDto): Seleccion {
  return {
    pregunta: dto.pregunta,
    opciones: dto.opciones.map((opcion) => ({ ...opcion })),
    comando: dto.comando,
    planillaId: dto.planilla_id,
    planillaNombre: dto.planilla_nombre,
  };
}

export function toEstadoChat(dto: EstadoChatDto): EstadoChat {
  return { seleccion: dto.seleccion ? toSeleccion(dto.seleccion) : null, deshacer: dto.deshacer };
}

export function toResultadoChat(dto: ResultadoChatDto): ResultadoChat {
  return {
    clientId: dto.client_id,
    comandos: dto.comandos,
    interpretadoPorIa: dto.interpretado_por_ia,
    respuestas: dto.respuestas.map(toRespuesta),
    estado: toEstadoChat(dto.estado),
    procesadoEn: dto.procesado_en,
  };
}
