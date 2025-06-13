# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class MobileRepairDashboard(models.TransientModel):
    """
    Dashboard completo para órdenes de reparación móvil.
    
    Proporciona una vista centralizada con KPIs, estadísticas y acciones rápidas
    para la gestión eficiente del taller de reparaciones.
    """
    _name = 'mobile.repair.dashboard'
    _description = 'Dashboard de Reparaciones Móviles'

    # ==========================================
    # CAMPOS DE FILTROS Y CONFIGURACIÓN
    # ==========================================
    
    date_from = fields.Date(
        string='Fecha Desde',
        default=lambda self: fields.Date.today().replace(day=1),
        help="Fecha de inicio para el análisis de datos"
    )
    
    date_to = fields.Date(
        string='Fecha Hasta',
        default=fields.Date.today,
        help="Fecha de fin para el análisis de datos"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        help="Moneda utilizada para los cálculos financieros"
    )

    # ==========================================
    # CAMPOS DE KPIs PRINCIPALES
    # ==========================================
    
    # --- KPIs de Volumen ---
    total_orders = fields.Integer(
        string='Total de Órdenes',
        compute='_compute_dashboard_data',
        store=False,
        help="Número total de órdenes en el período seleccionado"
    )
    
    orders_draft = fields.Integer(
        string='Órdenes Recibidas',
        compute='_compute_dashboard_data',
        store=False,
        help="Órdenes recibidas pendientes de iniciar"
    )
    
    orders_in_progress = fields.Integer(
        string='En Reparación',
        compute='_compute_dashboard_data',
        store=False,
        help="Órdenes actualmente en proceso de reparación"
    )
    
    orders_completed = fields.Integer(
        string='Completadas',
        compute='_compute_dashboard_data',
        store=False,
        help="Órdenes terminadas (listas para entrega + entregadas)"
    )
    
    orders_ready = fields.Integer(
        string='Listas para Entrega',
        compute='_compute_dashboard_data',
        store=False,
        help="Órdenes completadas pendientes de entrega"
    )
    
    orders_delivered = fields.Integer(
        string='Entregadas',
        compute='_compute_dashboard_data',
        store=False,
        help="Órdenes ya entregadas al cliente"
    )
    
    orders_canceled = fields.Integer(
        string='Canceladas',
        compute='_compute_dashboard_data',
        store=False,
        help="Órdenes canceladas por diferentes motivos"
    )
    
    orders_urgent = fields.Integer(
        string='Urgentes',
        compute='_compute_dashboard_data',
        store=False,
        help="Órdenes marcadas como urgentes"
    )

    # --- KPIs Financieros ---
    total_revenue = fields.Monetary(
        string='Ingresos Totales',
        compute='_compute_dashboard_data',
        currency_field='currency_id',
        store=False,
        help="Suma total de ingresos en el período"
    )
    
    avg_order_value = fields.Monetary(
        string='Valor Promedio por Orden',
        compute='_compute_dashboard_data',
        currency_field='currency_id',
        store=False,
        help="Valor promedio por orden de reparación"
    )
    
    pending_revenue = fields.Monetary(
        string='Ingresos Pendientes',
        compute='_compute_dashboard_data',
        currency_field='currency_id',
        store=False,
        help="Ingresos de órdenes completadas sin facturar"
    )

    # --- KPIs de Tiempo y Eficiencia ---
    avg_duration_hours = fields.Float(
        string='Duración Promedio (Horas)',
        compute='_compute_dashboard_data',
        store=False,
        help="Tiempo promedio de reparación en horas"
    )
    
    completion_rate = fields.Float(
        string='Tasa de Finalización (%)',
        compute='_compute_dashboard_data',
        store=False,
        help="Porcentaje de órdenes completadas vs iniciadas"
    )

    # --- KPIs de Análisis ---
    most_common_failure = fields.Char(
        string='Falla Más Común',
        compute='_compute_dashboard_data',
        store=False,
        help="Tipo de falla más frecuente en el período"
    )
    
    busiest_technician = fields.Char(
        string='Técnico Más Ocupado',
        compute='_compute_dashboard_data',
        store=False,
        help="Técnico con más órdenes asignadas"
    )

    # ==========================================
    # MÉTODOS DE CONFIGURACIÓN INICIAL
    # ==========================================

    @api.model
    def default_get(self, fields_list):
        """
        Establece valores por defecto al crear el dashboard.
        Configura el período de análisis al mes actual.
        """
        res = super().default_get(fields_list)
        
        # Configurar período por defecto (primer día del mes hasta hoy)
        today = fields.Date.today()
        first_day_of_month = today.replace(day=1)
        
        if 'date_from' in fields_list:
            res['date_from'] = first_day_of_month
        if 'date_to' in fields_list:
            res['date_to'] = today
            
        return res

    # ==========================================
    # MÉTODOS DE CÁLCULO PRINCIPAL
    # ==========================================

    @api.depends('date_from', 'date_to')
    def _compute_dashboard_data(self):
        """
        Método principal para calcular todos los KPIs del dashboard.
        
        Realiza cálculos seguros con validaciones para evitar errores
        y proporciona datos consistentes para la toma de decisiones.
        """
        for record in self:
            try:
                # Verificar disponibilidad del modelo principal
                if 'mobile.repair.order' not in self.env:
                    _logger.warning("Modelo mobile.repair.order no disponible")
                    record._set_default_values()
                    continue
                
                # Obtener órdenes del período con validación
                orders = record._get_filtered_orders()
                
                if not orders:
                    record._set_default_values()
                    continue
                
                # Calcular KPIs por categorías
                record._compute_volume_kpis(orders)
                record._compute_financial_kpis(orders)
                record._compute_efficiency_kpis(orders)
                record._compute_analysis_kpis(orders)
                
                _logger.info(f"Dashboard calculado: {len(orders)} órdenes procesadas")
                
            except Exception as e:
                _logger.error(f"Error calculando dashboard: {e}")
                record._set_default_values()

    def _get_filtered_orders(self):
        """
        Obtiene las órdenes filtradas por el período seleccionado.
        
        Returns:
            recordset: Órdenes de reparación en el período
        """
        domain = []
        
        # Aplicar filtros de fecha con validación
        if self.date_from:
            domain.append(('repair_date', '>=', 
                         fields.Datetime.combine(self.date_from, datetime.min.time())))
        
        if self.date_to:
            domain.append(('repair_date', '<=', 
                         fields.Datetime.combine(self.date_to, datetime.max.time())))
        
        # Buscar órdenes con manejo de errores
        try:
            orders = self.env['mobile.repair.order'].search(domain)
            return orders
        except Exception as e:
            _logger.error(f"Error obteniendo órdenes: {e}")
            return self.env['mobile.repair.order']

    # ==========================================
    # MÉTODOS DE CÁLCULO POR CATEGORÍAS
    # ==========================================

    def _compute_volume_kpis(self, orders):
        """
        Calcula KPIs relacionados con volumen de órdenes.
        
        Args:
            orders: Recordset de órdenes a analizar
        """
        self.total_orders = len(orders)
        
        # Contadores por estado con validación
        self.orders_draft = len(orders.filtered(lambda o: o.status == 'draft'))
        self.orders_in_progress = len(orders.filtered(lambda o: o.status == 'in_progress'))
        self.orders_ready = len(orders.filtered(lambda o: o.status == 'completed'))
        self.orders_delivered = len(orders.filtered(lambda o: o.status == 'delivered'))
        self.orders_canceled = len(orders.filtered(lambda o: o.status == 'canceled'))
        
        # Total de completadas (listas + entregadas)
        self.orders_completed = self.orders_ready + self.orders_delivered
        
        # Órdenes urgentes (cualquier estado activo)
        active_orders = orders.filtered(lambda o: o.status not in ['delivered', 'canceled'])
        self.orders_urgent = len(active_orders.filtered(lambda o: o.priority == 'urgent'))

    def _compute_financial_kpis(self, orders):
        """
        Calcula KPIs financieros con validaciones.
        
        Args:
            orders: Recordset de órdenes a analizar
        """
        # Ingresos totales con validación de campo
        order_amounts = orders.mapped('total_amount')
        self.total_revenue = sum(amount for amount in order_amounts if amount) if order_amounts else 0.0
        
        # Valor promedio por orden (evitar división por cero)
        if self.total_orders > 0 and self.total_revenue > 0:
            self.avg_order_value = self.total_revenue / self.total_orders
        else:
            self.avg_order_value = 0.0
        
        # Ingresos pendientes (órdenes completadas sin facturar)
        ready_orders = orders.filtered(lambda o: o.status == 'completed' and not o.invoice_id)
        ready_amounts = ready_orders.mapped('total_amount')
        self.pending_revenue = sum(amount for amount in ready_amounts if amount) if ready_amounts else 0.0

    def _compute_efficiency_kpis(self, orders):
        """
        Calcula KPIs de eficiencia y tiempo.
        
        Args:
            orders: Recordset de órdenes a analizar
        """
        # Duración promedio de reparaciones completadas
        completed_orders = orders.filtered(
            lambda o: o.status in ['completed', 'delivered'] 
                     and o.duration_hours 
                     and o.duration_hours > 0
        )
        
        if completed_orders:
            total_duration = sum(completed_orders.mapped('duration_hours'))
            self.avg_duration_hours = total_duration / len(completed_orders)
        else:
            self.avg_duration_hours = 0.0
        
        # Tasa de finalización (completadas vs iniciadas)
        started_orders = orders.filtered(lambda o: o.status != 'draft')
        if started_orders:
            completed_count = len(orders.filtered(lambda o: o.status in ['completed', 'delivered']))
            self.completion_rate = (completed_count / len(started_orders)) * 100
        else:
            self.completion_rate = 0.0

    def _compute_analysis_kpis(self, orders):
        """
        Calcula KPIs de análisis y tendencias.
        
        Args:
            orders: Recordset de órdenes a analizar
        """
        # Falla más común
        self.most_common_failure = self._get_most_common_failure(orders)
        
        # Técnico más ocupado
        self.busiest_technician = self._get_busiest_technician(orders)

    def _get_most_common_failure(self, orders):
        """
        Encuentra el tipo de falla más común.
        
        Args:
            orders: Recordset de órdenes
            
        Returns:
            str: Descripción de la falla más común
        """
        if not orders:
            return "Sin datos"
        
        # Contar fallas por tipo
        failure_counts = {}
        valid_orders = orders.filtered('failure_type_id')
        
        for order in valid_orders:
            failure_name = order.failure_type_id.name
            failure_counts[failure_name] = failure_counts.get(failure_name, 0) + 1
        
        if not failure_counts:
            return "Sin datos"
        
        # Encontrar la más común
        most_common = max(failure_counts, key=failure_counts.get)
        count = failure_counts[most_common]
        percentage = (count / len(valid_orders)) * 100
        
        return f"{most_common} ({count} casos, {percentage:.1f}%)"

    def _get_busiest_technician(self, orders):
        """
        Encuentra el técnico con más órdenes asignadas.
        
        Args:
            orders: Recordset de órdenes
            
        Returns:
            str: Información del técnico más ocupado
        """
        if not orders:
            return "Sin datos"
        
        # Contar órdenes por técnico
        technician_counts = {}
        active_orders = orders.filtered(lambda o: o.technician_id and o.status in ['draft', 'in_progress'])
        
        for order in active_orders:
            tech_name = order.technician_id.name
            technician_counts[tech_name] = technician_counts.get(tech_name, 0) + 1
        
        if not technician_counts:
            return "Sin asignaciones"
        
        # Encontrar el más ocupado
        busiest = max(technician_counts, key=technician_counts.get)
        count = technician_counts[busiest]
        
        return f"{busiest} ({count} órdenes activas)"

    # ==========================================
    # MÉTODOS DE UTILIDAD
    # ==========================================

    def _set_default_values(self):
        """
        Establece valores por defecto seguros en caso de error.
        """
        # KPIs de volumen
        self.total_orders = 0
        self.orders_draft = 0
        self.orders_in_progress = 0
        self.orders_completed = 0
        self.orders_ready = 0
        self.orders_delivered = 0
        self.orders_canceled = 0
        self.orders_urgent = 0
        
        # KPIs financieros
        self.total_revenue = 0.0
        self.avg_order_value = 0.0
        self.pending_revenue = 0.0
        
        # KPIs de eficiencia
        self.avg_duration_hours = 0.0
        self.completion_rate = 0.0
        
        # KPIs de análisis
        self.most_common_failure = "Sin datos"
        self.busiest_technician = "Sin datos"

    def _get_date_domain(self):
        """
        Genera el dominio de fechas para filtros.
        
        Returns:
            list: Dominio de búsqueda basado en las fechas seleccionadas
        """
        domain = []
        
        if self.date_from:
            domain.append(('repair_date', '>=', 
                         fields.Datetime.combine(self.date_from, datetime.min.time())))
        
        if self.date_to:
            domain.append(('repair_date', '<=', 
                         fields.Datetime.combine(self.date_to, datetime.max.time())))
        
        return domain

    # ==========================================
    # ACCIONES DEL DASHBOARD
    # ==========================================

    def action_refresh_data(self):
        """
        Actualiza manualmente los datos del dashboard.
        
        Returns:
            dict: Acción para recargar la vista actual
        """
        # Forzar recálculo
        self._compute_dashboard_data()
        
        # Mensaje de confirmación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '🔄 Datos Actualizados',
                'message': f'Dashboard actualizado con datos del período {self.date_from} - {self.date_to}',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_repair_orders(self):
        """Acción: Ver todas las órdenes del período"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de Reparación',
            'res_model': 'mobile.repair.order',
            'view_mode': 'tree,form,kanban',
            'target': 'current',
            'domain': self._get_date_domain(),
            'context': {'search_default_group_status': 1}
        }

    def action_view_draft_orders(self):
        """Acción: Ver órdenes recibidas (borradores)"""
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
        """Acción: Ver órdenes en proceso"""
        domain = self._get_date_domain()
        domain.append(('status', '=', 'in_progress'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes en Reparación',
            'res_model': 'mobile.repair.order',
            'view_mode': 'kanban,tree,form',
            'target': 'current',
            'domain': domain,
            'context': {'search_default_group_technician': 1}
        }

    def action_view_completed_orders(self):
        """Acción: Ver órdenes completadas (listas + entregadas)"""
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

    def action_view_ready_orders(self):
        """Acción: Ver órdenes listas para entrega"""
        domain = self._get_date_domain()
        domain.append(('status', '=', 'completed'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Listas para Entrega',
            'res_model': 'mobile.repair.order',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain,
            'context': {'search_default_not_invoiced': 1}
        }

    def action_view_urgent_orders(self):
        """Acción: Ver órdenes urgentes"""
        domain = self._get_date_domain()
        domain.extend([
            ('priority', '=', 'urgent'),
            ('status', 'not in', ['delivered', 'canceled'])
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes Urgentes',
            'res_model': 'mobile.repair.order',
            'view_mode': 'kanban,tree,form',
            'target': 'current',
            'domain': domain,
        }

    def action_create_repair_order(self):
        """Acción: Crear nueva orden de reparación"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Orden de Reparación',
            'res_model': 'mobile.repair.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_repair_date': fields.Datetime.now(),
                'default_priority': 'normal'
            }
        }

    def action_view_pending_invoices(self):
        """Acción: Ver órdenes pendientes de facturar"""
        domain = self._get_date_domain()
        domain.extend([
            ('status', '=', 'completed'),
            ('invoice_id', '=', False),
            ('total_amount', '>', 0)
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pendientes de Facturar',
            'res_model': 'mobile.repair.order',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain,
        }

    def action_view_technician_workload(self):
        """Acción: Ver carga de trabajo por técnico"""
        domain = self._get_date_domain()
        domain.append(('status', 'in', ['draft', 'in_progress']))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Carga de Trabajo por Técnico',
            'res_model': 'mobile.repair.order',
            'view_mode': 'kanban,tree',
            'target': 'current',
            'domain': domain,
            'context': {'search_default_group_technician': 1}
        }

    # ==========================================
    # MÉTODOS DE CONFIGURACIÓN AVANZADA
    # ==========================================

    def action_set_current_week(self):
        """Configura el filtro para la semana actual"""
        today = fields.Date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        self.write({
            'date_from': week_start,
            'date_to': week_end
        })
        
        return self.action_refresh_data()

    def action_set_current_month(self):
        """Configura el filtro para el mes actual"""
        today = fields.Date.today()
        month_start = today.replace(day=1)
        
        # Calcular último día del mes
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        self.write({
            'date_from': month_start,
            'date_to': month_end
        })
        
        return self.action_refresh_data()

    def action_set_last_30_days(self):
        """Configura el filtro para los últimos 30 días"""
        today = fields.Date.today()
        start_date = today - timedelta(days=30)
        
        self.write({
            'date_from': start_date,
            'date_to': today
        })
        
        return self.action_refresh_data()