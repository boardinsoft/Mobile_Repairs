# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta


class RepairDashboard(models.TransientModel):
    """
    Modelo para el dashboard de estadísticas de reparaciones.
    """
    _name = 'mobile.repair.dashboard'
    _description = 'Dashboard de Reparaciones'

    # ✅ FILTROS DE FECHA
    date_from = fields.Date(
        string='Desde',
        default=lambda self: fields.Date.today().replace(day=1),  # Primer día del mes
        required=True
    )
    date_to = fields.Date(
        string='Hasta',
        default=fields.Date.today,
        required=True
    )

    # ✅ ESTADÍSTICAS GENERALES
    total_orders = fields.Integer(
        string='Total Órdenes',
        compute='_compute_statistics'
    )
    orders_draft = fields.Integer(
        string='Borradores',
        compute='_compute_statistics'
    )
    orders_in_progress = fields.Integer(
        string='En Proceso',
        compute='_compute_statistics'
    )
    orders_completed = fields.Integer(
        string='Completadas',
        compute='_compute_statistics'
    )
    orders_canceled = fields.Integer(
        string='Canceladas',
        compute='_compute_statistics'
    )

    # ✅ ESTADÍSTICAS DE TIEMPO
    avg_duration_hours = fields.Float(
        string='Duración Promedio (Horas)',
        compute='_compute_statistics'
    )
    total_revenue = fields.Monetary(
        string='Ingresos Totales',
        compute='_compute_statistics'
    )
    avg_order_value = fields.Monetary(
        string='Valor Promedio por Orden',
        compute='_compute_statistics'
    )

    # ✅ ESTADÍSTICAS DE FALLAS
    most_common_failure = fields.Char(
        string='Falla Más Común',
        compute='_compute_statistics'
    )
    failure_stats_ids = fields.One2many(
        'mobile.repair.failure.stat',
        'dashboard_id',
        string='Estadísticas de Fallas',
        compute='_compute_statistics'
    )

    # ✅ ESTADÍSTICAS DE TÉCNICOS
    technician_stats_ids = fields.One2many(
        'mobile.repair.technician.stat',
        'dashboard_id',
        string='Estadísticas de Técnicos',
        compute='_compute_statistics'
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('date_from', 'date_to')
    def _compute_statistics(self):
        """
        Calcula todas las estadísticas del dashboard con protección robusta.
        """
        for record in self:
            # Dominio base para filtrar por fechas
            domain = [
                ('repair_date', '>=', record.date_from),
                ('repair_date', '<=', record.date_to)
            ]

            # Buscar todas las órdenes en el rango de fechas
            orders = self.env['mobile.repair.order'].search(domain)
            total_orders_count = len(orders)

            # ✅ ESTADÍSTICAS GENERALES con protección
            record.total_orders = total_orders_count
            record.orders_draft = len(orders.filtered(lambda o: o.status == 'draft'))
            record.orders_in_progress = len(orders.filtered(lambda o: o.status == 'in_progress'))
            record.orders_completed = len(orders.filtered(lambda o: o.status == 'completed'))
            record.orders_canceled = len(orders.filtered(lambda o: o.status == 'canceled'))

            # ✅ ESTADÍSTICAS FINANCIERAS con protección robusta
            total_revenue = sum(orders.mapped('total_amount')) if orders else 0.0
            record.total_revenue = total_revenue
            
            # Protección contra división por cero mejorada
            if total_orders_count > 0 and total_revenue > 0:
                record.avg_order_value = total_revenue / total_orders_count
            else:
                record.avg_order_value = 0.0

            # ✅ ESTADÍSTICAS DE TIEMPO con múltiples validaciones
            completed_orders = orders.filtered(
                lambda o: (
                    o.status == 'completed' and 
                    o.duration_hours is not False and 
                    o.duration_hours > 0
                )
            )
            
            if completed_orders:
                total_duration = sum(completed_orders.mapped('duration_hours'))
                completed_count = len(completed_orders)
                # Doble verificación para evitar división por cero
                if completed_count > 0 and total_duration >= 0:
                    record.avg_duration_hours = total_duration / completed_count
                else:
                    record.avg_duration_hours = 0.0
            else:
                record.avg_duration_hours = 0.0

            # ✅ ESTADÍSTICAS DE FALLAS Y TÉCNICOS
            record._compute_failure_statistics_safe(orders)
            record._compute_technician_statistics_safe(orders)

    def _compute_failure_statistics_safe(self, orders):
        """
        Calcula estadísticas de tipos de fallas con protección completa.
        """
        if not orders:
            self.most_common_failure = "N/A"
            self.failure_stats_ids = [(5, 0, 0)]  # Limpiar registros existentes
            return
        
        # Contar fallas por tipo con validación
        failure_counts = {}
        valid_orders_count = 0

        for order in orders:
            if order.failure_type_id and order.failure_type_id.name:
                failure_name = order.failure_type_id.name
                failure_counts[failure_name] = failure_counts.get(failure_name, 0) + 1
                valid_orders_count += 1

        # Encontrar la falla más común
        if failure_counts:
            self.most_common_failure = max(failure_counts, key=failure_counts.get)
        else:
            self.most_common_failure = "N/A"

        # Crear registros de estadísticas de fallas
        failure_stats = []
        total_orders_with_failures = max(valid_orders_count, 1)  # Evitar división por cero
    
        for failure_type, count in failure_counts.items():
            # Protección robusta para el cálculo de porcentaje
            try:
                percentage = (count / total_orders_with_failures) * 100
                # Validar que el porcentaje esté en rango válido
                percentage = max(0.0, min(100.0, percentage))
            except (ZeroDivisionError, TypeError, ValueError):
                percentage = 0.0
            
            failure_stats.append((0, 0, {
                'failure_type': failure_type or 'Sin especificar',
                'count': max(0, count),  # Asegurar que count no sea negativo
                'percentage': percentage
            }))
        
        self.failure_stats_ids = failure_stats

    def _compute_technician_statistics_safe(self, orders):
        """
        Calcula estadísticas de técnicos con protección completa contra errores.
        """
        if not orders:
            self.technician_stats_ids = [(5, 0, 0)]  # Limpiar registros existentes
            return

        # Agrupar por técnico con validaciones
        technician_stats = {}
        
        for order in orders:
            # Validar que el técnico existe y tiene nombre
            if not order.technician_id or not order.technician_id.name:
                continue
                
            tech_name = order.technician_id.name
            
            # Inicializar estadísticas del técnico si no existe
            if tech_name not in technician_stats:
                technician_stats[tech_name] = {
                    'orders_count': 0,
                    'completed_count': 0,
                    'total_duration': 0.0,
                    'total_revenue': 0.0
                }

            # Actualizar contadores con validaciones
            technician_stats[tech_name]['orders_count'] += 1
            
            # Validar y sumar ingresos
            order_amount = order.total_amount if order.total_amount else 0.0
            technician_stats[tech_name]['total_revenue'] += order_amount

            # Procesar órdenes completadas
            if order.status == 'completed':
                technician_stats[tech_name]['completed_count'] += 1
                
                # Validar duración antes de sumar
                duration = order.duration_hours if (
                    order.duration_hours is not False and 
                    order.duration_hours >= 0
                ) else 0.0
                technician_stats[tech_name]['total_duration'] += duration

        # Crear registros de estadísticas de técnicos
        tech_stats = []
        for tech_name, stats in technician_stats.items():
            # Cálculos con protección robusta
            try:
                # Duración promedio
                if stats['completed_count'] > 0 and stats['total_duration'] >= 0:
                    avg_duration = stats['total_duration'] / stats['completed_count']
                    avg_duration = max(0.0, avg_duration)  # No puede ser negativo
                else:
                    avg_duration = 0.0
                
                # Tasa de finalización
                if stats['orders_count'] > 0:
                    completion_rate = (stats['completed_count'] / stats['orders_count']) * 100
                    completion_rate = max(0.0, min(100.0, completion_rate))  # Entre 0 y 100
                else:
                    completion_rate = 0.0
                    
            except (ZeroDivisionError, TypeError, ValueError) as e:
                # Log del error para debugging
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando estadísticas para técnico {tech_name}: {e}")
                avg_duration = 0.0
                completion_rate = 0.0

            tech_stats.append((0, 0, {
                'technician_name': tech_name,
                'orders_count': max(0, stats['orders_count']),
                'completed_count': max(0, stats['completed_count']),
                'avg_duration': avg_duration,
                'completion_rate': completion_rate,
                'total_revenue': max(0.0, stats['total_revenue'])
            }))

        self.technician_stats_ids = tech_stats

    def action_refresh_data(self):
        """
        Acción para refrescar los datos del dashboard.
        """
        self._compute_statistics()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }


class RepairFailureStat(models.TransientModel):
    """
    Modelo auxiliar para estadísticas de fallas.
    """
    _name = 'mobile.repair.failure.stat'
    _description = 'Estadística de Fallas'

    dashboard_id = fields.Many2one('mobile.repair.dashboard')
    failure_type = fields.Char(string='Tipo de Falla')
    count = fields.Integer(string='Cantidad')
    percentage = fields.Float(string='Porcentaje')


class RepairTechnicianStat(models.TransientModel):
    """
    Modelo auxiliar para estadísticas de técnicos.
    """
    _name = 'mobile.repair.technician.stat'
    _description = 'Estadística de Técnicos'

    dashboard_id = fields.Many2one('mobile.repair.dashboard')
    technician_name = fields.Char(string='Técnico')
    orders_count = fields.Integer(string='Total Órdenes')
    completed_count = fields.Integer(string='Completadas')
    avg_duration = fields.Float(string='Duración Promedio (h)')
    completion_rate = fields.Float(string='Tasa de Finalización (%)')
    total_revenue = fields.Monetary(string='Ingresos Generados')
    currency_id = fields.Many2one('res.currency', related='dashboard_id.currency_id')