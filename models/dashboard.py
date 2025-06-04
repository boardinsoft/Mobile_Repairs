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
        Calcula todas las estadísticas del dashboard.
        """
        for record in self:
            # Dominio base para filtrar por fechas
            domain = [
                ('repair_date', '>=', record.date_from),
                ('repair_date', '<=', record.date_to)
            ]

            # Buscar todas las órdenes en el rango de fechas
            orders = self.env['mobile.repair.order'].search(domain)

            # ✅ ESTADÍSTICAS GENERALES
            record.total_orders = len(orders)
            record.orders_draft = len(orders.filtered(lambda o: o.status == 'draft'))
            record.orders_in_progress = len(orders.filtered(lambda o: o.status == 'in_progress'))
            record.orders_completed = len(orders.filtered(lambda o: o.status == 'completed'))
            record.orders_canceled = len(orders.filtered(lambda o: o.status == 'canceled'))

            # ✅ ESTADÍSTICAS FINANCIERAS
            record.total_revenue = sum(orders.mapped('total_amount'))
            record.avg_order_value = record.total_revenue / len(orders) if orders else 0

            # ✅ ESTADÍSTICAS DE TIEMPO
            completed_orders = orders.filtered(lambda o: o.status == 'completed' and o.duration_hours > 0)
            record.avg_duration_hours = sum(completed_orders.mapped('duration_hours')) / len(completed_orders) if completed_orders else 0

            # ✅ ESTADÍSTICAS DE FALLAS
            record._compute_failure_statistics(orders)
            record._compute_technician_statistics(orders)

    def _compute_failure_statistics(self, orders):
        """
        Calcula estadísticas de tipos de fallas.
        ✅ CORREGIDO: Usa failure_type_id en lugar de failure_type
        """
        # Contar fallas por tipo
        failure_counts = {}
        for order in orders:
            # ✅ CORRECCIÓN: Usar failure_type_id que es un Many2one
            if order.failure_type_id:
                failure_name = order.failure_type_id.name
                failure_counts[failure_name] = failure_counts.get(failure_name, 0) + 1

        # Encontrar la falla más común
        if failure_counts:
            self.most_common_failure = max(failure_counts, key=failure_counts.get)
        else:
            self.most_common_failure = "N/A"

        # Crear registros de estadísticas de fallas (para gráficos futuros)
        failure_stats = []
        for failure_type, count in failure_counts.items():
            percentage = (count / len(orders)) * 100 if orders else 0
            failure_stats.append((0, 0, {
                'failure_type': failure_type,
                'count': count,
                'percentage': percentage
            }))
        self.failure_stats_ids = failure_stats

    def _compute_technician_statistics(self, orders):
        """
        Calcula estadísticas de técnicos.
        """
        # Agrupar por técnico
        technician_stats = {}
        for order in orders:
            if order.technician_id:
                tech_name = order.technician_id.name
                if tech_name not in technician_stats:
                    technician_stats[tech_name] = {
                        'orders_count': 0,
                        'completed_count': 0,
                        'total_duration': 0,
                        'total_revenue': 0
                    }

                technician_stats[tech_name]['orders_count'] += 1
                technician_stats[tech_name]['total_revenue'] += order.total_amount

                if order.status == 'completed':
                    technician_stats[tech_name]['completed_count'] += 1
                    technician_stats[tech_name]['total_duration'] += order.duration_hours

        # Crear registros de estadísticas de técnicos
        tech_stats = []
        for tech_name, stats in technician_stats.items():
            avg_duration = stats['total_duration'] / stats['completed_count'] if stats['completed_count'] else 0
            completion_rate = (stats['completed_count'] / stats['orders_count']) * 100 if stats['orders_count'] else 0

            tech_stats.append((0, 0, {
                'technician_name': tech_name,
                'orders_count': stats['orders_count'],
                'completed_count': stats['completed_count'],
                'avg_duration': avg_duration,
                'completion_rate': completion_rate,
                'total_revenue': stats['total_revenue']
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