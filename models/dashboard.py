# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class MobileRepairDashboard(models.TransientModel):
    """Dashboard para órdenes de reparación móvil"""
    _name = 'mobile.repair.dashboard'
    _description = 'Dashboard de Reparaciones Móviles'

    # Campos básicos de KPIs
    total_orders = fields.Integer(
        string='Total de Órdenes',
        compute='_compute_dashboard_data',
        store=False
    )
    
    orders_draft = fields.Integer(
        string='Órdenes en Borrador',
        compute='_compute_dashboard_data',
        store=False
    )
    
    orders_in_progress = fields.Integer(
        string='Órdenes en Proceso',
        compute='_compute_dashboard_data',
        store=False
    )
    
    orders_completed = fields.Integer(
        string='Órdenes Completadas',
        compute='_compute_dashboard_data',
        store=False
    )
    
    orders_canceled = fields.Integer(
        string='Órdenes Canceladas',
        compute='_compute_dashboard_data',
        store=False
    )
    
    total_revenue = fields.Monetary(
        string='Ingresos Totales',
        compute='_compute_dashboard_data',
        currency_field='currency_id',
        store=False
    )
    
    avg_duration_hours = fields.Float(
        string='Duración Promedio (Horas)',
        compute='_compute_dashboard_data',
        store=False
    )
    
    avg_order_value = fields.Monetary(
        string='Valor Promedio por Orden',
        compute='_compute_dashboard_data',
        currency_field='currency_id',
        store=False
    )
    
    most_common_failure = fields.Char(
        string='Falla Más Común',
        compute='_compute_dashboard_data',
        store=False
    )
    
    # Campos para filtros
    date_from = fields.Date(
        string='Fecha Desde',
        default=lambda self: fields.Date.today().replace(day=1)
    )
    
    date_to = fields.Date(
        string='Fecha Hasta',
        default=fields.Date.today
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )

    @api.model
    def default_get(self, fields_list):
        """Establecer valores por defecto al crear el dashboard"""
        res = super().default_get(fields_list)
        
        # Establecer fechas por defecto (primer día del mes hasta hoy)
        today = fields.Date.today()
        first_day_of_month = today.replace(day=1)
        
        if 'date_from' in fields_list:
            res['date_from'] = first_day_of_month
        if 'date_to' in fields_list:
            res['date_to'] = today
            
        return res

    @api.depends('date_from', 'date_to')
<<<<<<< HEAD
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
=======
    def _compute_dashboard_data(self):
        """Computar todos los datos del dashboard"""
        for record in self:
            try:
                # Verificar si el modelo existe
                if 'mobile.repair.order' not in self.env:
                    record._set_default_values()
                    continue
                
                # Dominio base para filtrar órdenes (usando repair_date que es el campo real)
                domain = []
                if record.date_from:
                    domain.append(('repair_date', '>=', fields.Datetime.combine(record.date_from, datetime.min.time())))
                if record.date_to:
                    domain.append(('repair_date', '<=', fields.Datetime.combine(record.date_to, datetime.max.time())))
                
                # Obtener todas las órdenes
                orders = self.env['mobile.repair.order'].search(domain)
                
                # KPIs básicos (usando los campos reales del modelo)
                record.total_orders = len(orders)
                record.orders_draft = len(orders.filtered(lambda o: o.status == 'draft'))
                record.orders_in_progress = len(orders.filtered(lambda o: o.status == 'in_progress'))
                record.orders_completed = len(orders.filtered(lambda o: o.status in ['completed', 'delivered']))
                record.orders_canceled = len(orders.filtered(lambda o: o.status == 'canceled'))
                
                # Ingresos totales (usando total_amount que es el campo real)
                record.total_revenue = sum(orders.mapped('total_amount'))
                
                # Duración promedio (usando duration_hours que existe en el modelo)
                completed_orders = orders.filtered(lambda o: o.duration_hours > 0)
                record.avg_duration_hours = (
                    sum(completed_orders.mapped('duration_hours')) / len(completed_orders)
                    if completed_orders else 0
                )
                
                # Valor promedio por orden
                record.avg_order_value = (
                    record.total_revenue / record.total_orders
                    if record.total_orders else 0
                )
                
                # Falla más común (usando failure_type_id que es el campo real)
                if orders.mapped('failure_type_id'):
                    failure_counts = {}
                    for order in orders:
                        if order.failure_type_id:
                            failure = order.failure_type_id.name
                            failure_counts[failure] = failure_counts.get(failure, 0) + 1
                    
                    if failure_counts:
                        most_common = max(failure_counts, key=failure_counts.get)
                        record.most_common_failure = f"{most_common} ({failure_counts[most_common]})"
                    else:
                        record.most_common_failure = "Sin datos"
                else:
                    record.most_common_failure = "Sin datos"
                    
            except Exception as e:
                # En caso de error, establecer valores por defecto
                record._set_default_values()
    
    def _set_default_values(self):
        """Establecer valores por defecto en caso de error"""
        self.total_orders = 0
        self.orders_draft = 0
        self.orders_in_progress = 0
        self.orders_completed = 0
        self.orders_canceled = 0
        self.total_revenue = 0.0
        self.avg_duration_hours = 0.0
        self.avg_order_value = 0.0
        self.most_common_failure = "Sin datos"
>>>>>>> stability

    def action_refresh_data(self):
        """Actualizar datos del dashboard"""
        # Recomputar los campos
        self._compute_dashboard_data()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # Métodos para los botones de navegación del dashboard
    def action_view_repair_orders(self):
        """Ver todas las órdenes de reparación"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de Reparación',
            'res_model': 'mobile.repair.order',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': self._get_date_domain(),
        }
    
    def action_view_draft_orders(self):
        """Ver órdenes en borrador (usando status del modelo real)"""
        domain = self._get_date_domain()
        domain.append(('status', '=', 'draft'))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes Recibidas',
            'res_model': 'mobile.repair.order',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain,
        }
    
    def action_view_progress_orders(self):
        """Ver órdenes en proceso (usando status del modelo real)"""
        domain = self._get_date_domain()
        domain.append(('status', '=', 'in_progress'))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes en Reparación',
            'res_model': 'mobile.repair.order',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain,
        }
    
    def action_view_completed_orders(self):
        """Ver órdenes completadas (usando status del modelo real)"""
        domain = self._get_date_domain()
        domain.append(('status', 'in', ['completed', 'delivered']))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes Completadas',
            'res_model': 'mobile.repair.order',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain,
        }
    
    def action_create_repair_order(self):
        """Crear nueva orden de reparación"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Orden de Reparación',
            'res_model': 'mobile.repair.order',
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_urgent_orders(self):
        """Ver órdenes urgentes (usando priority del modelo real)"""
        domain = self._get_date_domain()
        domain.append(('priority', '=', 'urgent'))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes Urgentes',
            'res_model': 'mobile.repair.order',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain,
        }
    
    def action_view_this_week_orders(self):
        """Ver órdenes de esta semana"""
        from datetime import datetime, timedelta
        today = fields.Date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        domain = [
            ('repair_date', '>=', fields.Datetime.combine(week_start, datetime.min.time())),
            ('repair_date', '<=', fields.Datetime.combine(week_end, datetime.max.time()))
        ]
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de Esta Semana',
            'res_model': 'mobile.repair.order',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain,
        }
    
    def action_view_devices(self):
        """Ver dispositivos móviles"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dispositivos Móviles',
            'res_model': 'mobile.device',
            'view_mode': 'tree,form',
            'target': 'current',
        }
    
    def action_view_fault_categories(self):
        """Ver categorías de fallas"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Categorías de Fallas',
            'res_model': 'mobile.fault.category',
            'view_mode': 'tree,form',
            'target': 'current',
        }
    
    def action_view_faults(self):
        """Ver tipos de fallas"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tipos de Fallas',
            'res_model': 'mobile.fault',
            'view_mode': 'tree,form',
            'target': 'current',
        }
    
    def _get_date_domain(self):
        """Obtener dominio de fechas basado en los filtros (usando repair_date)"""
        domain = []
        if self.date_from:
            domain.append(('repair_date', '>=', fields.Datetime.combine(self.date_from, datetime.min.time())))
        if self.date_to:
            domain.append(('repair_date', '<=', fields.Datetime.combine(self.date_to, datetime.max.time())))
        return domain