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