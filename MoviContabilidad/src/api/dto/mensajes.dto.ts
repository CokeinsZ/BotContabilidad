export interface RespuestaDto {
  tipo: 'exito' | 'aviso' | 'error' | 'info' | 'seleccion';
  texto: string;
}

export interface OpcionDto {
  valor: number;
  etiqueta: string;
  crea: boolean;
}

export interface SeleccionDto {
  pregunta: string;
  opciones: OpcionDto[];
  comando: string;
  planilla_id: string | null;
  planilla_nombre: string | null;
}

export interface EstadoChatDto {
  seleccion: SeleccionDto | null;
  deshacer: string | null;
}

export interface ResultadoChatDto {
  client_id: string | null;
  comandos: string[];
  interpretado_por_ia: boolean;
  respuestas: RespuestaDto[];
  estado: EstadoChatDto;
  procesado_en: string;
}
