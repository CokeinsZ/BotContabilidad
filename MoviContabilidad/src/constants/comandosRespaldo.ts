import type { Comando } from '@/api/entities';

/**
 * Catálogo local por si `GET /app/comandos` falla (mismo orden y datos que
 * `src/mobile/catalog.py` del bot). El servidor es la fuente de verdad.
 */
export const COMANDOS_RESPALDO: Comando[] = [
  { id: 'gasto', etiqueta: 'Gasto', icono: 'gasto', argumentos: 'monto_texto', ejemplo: '5.000 pan', ayuda: 'Compras a proveedores', confirmar: false, sugiereTrabajador: false, alias: ['g'] },
  { id: 'efectivo', etiqueta: 'Efectivo', icono: 'efectivo', argumentos: 'monto', ejemplo: '350.000', ayuda: 'Efectivo de las ventas del día', confirmar: false, sugiereTrabajador: false, alias: ['e'] },
  { id: 'saldo', etiqueta: 'Saldo', icono: 'saldo', argumentos: 'monto', ejemplo: '1.200.000', ayuda: 'Dinero físico en caja', confirmar: false, sugiereTrabajador: false, alias: ['saldos', 's'] },
  { id: 'trabajador', etiqueta: 'Préstamo', icono: 'prestamo', argumentos: 'monto_trabajador', ejemplo: '20.000 juan', ayuda: 'Préstamo a un trabajador (también queda en su archivo)', confirmar: false, sugiereTrabajador: true, alias: ['trabajadores', 't'] },
  { id: 'retiro', etiqueta: 'Retiro', icono: 'retiro', argumentos: 'monto_texto', ejemplo: '100.000 banco', ayuda: "Sacar dinero de la caja. 'nomina <nombre>' también cierra el período", confirmar: false, sugiereTrabajador: false, alias: ['r'] },
  { id: 'limpieza', etiqueta: 'Aseo', icono: 'aseo', argumentos: 'monto', ejemplo: '8.000', ayuda: 'Productos de aseo y limpieza', confirmar: false, sugiereTrabajador: false, alias: ['aseo', 'aseos', 'l'] },
  { id: 'alimentacion', etiqueta: 'Alimentación', icono: 'alimentacion', argumentos: 'monto', ejemplo: '30.000', ayuda: 'Comida del personal', confirmar: false, sugiereTrabajador: false, alias: ['alimentaciones', 'alimentación', 'comida', 'a'] },
  { id: 'administrador', etiqueta: 'Vale admin', icono: 'administrador', argumentos: 'monto', ejemplo: '20.000', ayuda: 'Vale del administrador', confirmar: false, sugiereTrabajador: false, alias: ['admin'] },
  { id: 'inversion', etiqueta: 'Inversión', icono: 'inversion', argumentos: 'monto_texto', ejemplo: '500.000 maquinaria', ayuda: 'Inversiones en el negocio', confirmar: false, sugiereTrabajador: false, alias: ['inversiones', 'inversión', 'inv'] },
  { id: 'nomina', etiqueta: 'Nómina', icono: 'nomina', argumentos: 'monto_trabajador', ejemplo: '200.000 juan', ayuda: 'Pago de nómina: cierra los préstamos del trabajador', confirmar: false, sugiereTrabajador: true, alias: ['nómina', 'n'] },
  { id: 'terminar_dia', etiqueta: 'Resumen', icono: 'resumen', argumentos: 'ninguno', ejemplo: '', ayuda: 'Totales de la planilla', confirmar: false, sugiereTrabajador: false, alias: ['resumen'] },
  { id: 'deshacer', etiqueta: 'Deshacer', icono: 'deshacer', argumentos: 'ninguno', ejemplo: '', ayuda: 'Revierte todo lo de tu último mensaje', confirmar: true, sugiereTrabajador: false, alias: ['undo'] },
  { id: 'corregir_saldos', etiqueta: 'Corregir saldos', icono: 'corregir_saldos', argumentos: 'ninguno', ejemplo: '', ayuda: 'Recalcula el saldo de todas las planillas siguientes a esta', confirmar: true, sugiereTrabajador: false, alias: ['corregir saldos', 'corregir_saldo', 'corregir saldo', 'recalcular_saldos'] },
];
