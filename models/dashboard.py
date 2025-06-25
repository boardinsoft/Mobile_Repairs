# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class RepairDashboard(models.TransientModel):
    """Dashboard minimalista para reparaciones móviles"""
    _name = 'mobile.repair.dashboard'
    _description = 'Dashboard de Reparaciones'

    # ============================================================
    # CAMPOS ESENCIALES (SOLO KPIs CLAVE)
    # ============================================================
    
    # Filtros de período
    date_from = fields.Date(
        string='Desde',
        default=lambda self: fields.Date.today().replace(day=1)
    )
    
    date_to = fields.Date(
        string='Hasta',
        default=fields.Date.today
    )
    
    # KPIs principales
    total_orders = fields.Integer(
        string='Total Órdenes',
        compute='_compute_kpis',
        help="Órdenes totales en el período"
    )
    
    pending_orders = fields.Integer(
        string='Pendientes',
        compute='_compute_kpis',
        help="Órdenes recibidas y en proceso"
    )
    
    completed_today = fields.Integer(
        string='Completadas Hoy',
        compute='_compute_kpis'
    )
    
    # Completadas esta semana
    completed_week = fields.Integer(
        string='Completadas Esta Semana',
        compute='_compute_kpis'
    )
    
    # Completadas este mes
    completed_month = fields.Integer(
        string='Completadas Este Mes',
        compute='_compute_kpis'
    )
    
    urgent_orders = fields.Integer(
        string='Urgentes',
        compute='_compute_kpis',
        help="Órdenes urgentes activas"
    )
    
    # Métricas financieras
    revenue_month = fields.Monetary(
        string='Ingresos del Mes',
        compute='_compute_kpis',
        currency_field='currency_id'
    )
    
    avg_duration = fields.Float(
        string='Duración Promedio (días)',
        compute='_compute_kpis'
    )
    
    # Información destacada
    top_technician = fields.Char(
        string='Técnico Destacado',
        compute='_compute_kpis'
    )
    
    # Nuevos KPIs - Órdenes por mes
    orders_by_month_data = fields.Text(
        string='Datos Órdenes por Mes',
        compute='_compute_chart_kpis'
    )
    
    # KPIs - Órdenes por técnico
    orders_by_technician_data = fields.Text(
        string='Datos Órdenes por Técnico',
        compute='_compute_chart_kpis'
    )
    
    # KPIs - Dispositivos más reparados
    top_devices_data = fields.Text(
        string='Dispositivos Más Reparados',
        compute='_compute_chart_kpis'
    )
    
    # Campos para mostrar top devices como texto
    most_repaired_device = fields.Char(
        string='Dispositivo Más Reparado',
        compute='_compute_chart_kpis'
    )
    
    total_devices_repaired = fields.Integer(
        string='Total Dispositivos Únicos',
        compute='_compute_chart_kpis'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    # ============================================================
    # CÁLCULO DE KPIS
    # ============================================================
    
    @api.depends('date_from', 'date_to')
    def _compute_kpis(self):
        """Calcula todos los KPIs de forma eficiente"""
        for record in self:
            RepairOrder = self.env['mobile.repair.order']
            
            # Dominio base con fechas
            domain = [
                ('date_received', '>=', record.date_from),
                ('date_received', '<=', record.date_to)
            ]
            
            # Total de órdenes en el período
            record.total_orders = RepairOrder.search_count(domain)
            
            # Órdenes pendientes
            record.pending_orders = RepairOrder.search_count(
                domain + [('state', 'in', ['draft', 'in_progress'])]
            )
            
            # Completadas hoy
            today = fields.Date.today()
            record.completed_today = RepairOrder.search_count([
                ('date_completed', '>=', today),
                ('date_completed', '<', today + timedelta(days=1))
            ])
            
            # Completadas esta semana
            week_start = today - timedelta(days=today.weekday())
            record.completed_week = RepairOrder.search_count([
                ('date_completed', '>=', week_start),
                ('date_completed', '<=', today)
            ])
            
            # Completadas este mes
            month_start = today.replace(day=1)
            record.completed_month = RepairOrder.search_count([
                ('date_completed', '>=', month_start),
                ('date_completed', '<=', today)
            ])
            
            # Urgentes activas
            record.urgent_orders = RepairOrder.search_count([
                ('priority', '=', 'urgent'),
                ('state', 'in', ['draft', 'in_progress'])
            ])
            
            # Ingresos del mes actual
            first_day_month = fields.Date.today().replace(day=1)
            completed_orders = RepairOrder.search([
                ('date_completed', '>=', first_day_month),
                ('state', 'in', ['ready', 'delivered']),
                ('final_cost', '>', 0)
            ])
            record.revenue_month = sum(completed_orders.mapped('final_cost'))
            
            # Duración promedio
            finished_orders = RepairOrder.search([
                ('date_completed', '!=', False),
                ('duration_days', '>', 0)
            ] + domain)
            
            if finished_orders:
                record.avg_duration = sum(finished_orders.mapped('duration_days')) / len(finished_orders)
            else:
                record.avg_duration = 0.0
            
            # Técnico más productivo (más órdenes completadas)
            record.top_technician = record._get_top_technician()

    def _get_top_technician(self):
        """Obtiene el técnico con más órdenes completadas en el período"""
        RepairOrder = self.env['mobile.repair.order']
        
        technician_data = RepairOrder.read_group(
            [
                ('date_completed', '>=', self.date_from),
                ('date_completed', '<=', self.date_to),
                ('technician_id', '!=', False),
                ('state', 'in', ['ready', 'delivered'])
            ],
            ['technician_id'],
            ['technician_id']
        )
        
        if technician_data:
            # Encuentra el técnico con más órdenes
            top = max(technician_data, key=lambda x: x['technician_id_count'])
            return f"{top['technician_id'][1]} ({top['technician_id_count']} completadas)"
        
        return "Sin datos"

    @api.depends('date_from', 'date_to')
    def _compute_chart_kpis(self):
        """Calcula datos para los nuevos KPIs de gráficos"""
        import json
        from collections import defaultdict
        
        for record in self:
            RepairOrder = self.env['mobile.repair.order']
            
            # 1. ÓRDENES POR MES (últimos 12 meses)
            orders_by_month = []
            today = fields.Date.today()
            
            for i in range(12):
                # Calcular primer y último día del mes
                if i == 0:
                    month_start = today.replace(day=1)
                    if today.month == 12:
                        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                else:
                    if today.month - i <= 0:
                        month_start = today.replace(year=today.year - 1, month=today.month - i + 12, day=1)
                    else:
                        month_start = today.replace(month=today.month - i, day=1)
                    
                    if month_start.month == 12:
                        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
                
                count = RepairOrder.search_count([
                    ('date_received', '>=', month_start),
                    ('date_received', '<=', month_end)
                ])
                
                orders_by_month.append({
                    'month': month_start.strftime('%m/%Y'),
                    'count': count,
                    'month_name': month_start.strftime('%B %Y')
                })
            
            record.orders_by_month_data = json.dumps(list(reversed(orders_by_month)))
            
            # 2. ÓRDENES POR TÉCNICO (activos)
            technician_data = RepairOrder.read_group(
                [('technician_id', '!=', False)],
                ['technician_id'],
                ['technician_id']
            )
            
            orders_by_technician = []
            for item in technician_data[:10]:  # Top 10 técnicos
                orders_by_technician.append({
                    'technician': item['technician_id'][1],
                    'count': item['technician_id_count']
                })
            
            record.orders_by_technician_data = json.dumps(orders_by_technician)
            
            # 3. DISPOSITIVOS MÁS REPARADOS
            device_data = RepairOrder.read_group(
                [('device_id', '!=', False)],
                ['device_brand', 'device_model'],
                ['device_brand', 'device_model']
            )
            
            # Agrupar por marca y modelo
            device_counts = defaultdict(int)
            for item in device_data:
                brand = item['device_brand'] or 'Sin marca'
                model = item['device_model'] or 'Sin modelo'
                device_key = f"{brand} {model}"
                device_counts[device_key] += item['__count']
            
            # Convertir a lista y ordenar
            top_devices = sorted(device_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            top_devices_list = []
            for device, count in top_devices:
                top_devices_list.append({
                    'device': device,
                    'count': count
                })
            
            record.top_devices_data = json.dumps(top_devices_list)
            
            # Campos individuales para mostrar en el dashboard
            if top_devices:
                record.most_repaired_device = f"{top_devices[0][0]} ({top_devices[0][1]} reparaciones)"
                record.total_devices_repaired = len(device_counts)
            else:
                record.most_repaired_device = "Sin datos"
                record.total_devices_repaired = 0

    # ============================================================
    # MÉTODOS DE DATOS PARA GRÁFICOS
    # ============================================================
    
    @api.model
    def get_kpi_chart_data(self):
        """Retorna datos específicos para gráficos KPI del dashboard mejorado"""
        RepairOrder = self.env['mobile.repair.order']
        today = fields.Date.today()
        
        # 1. Órdenes completadas por período (hoy, semana, mes)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        completed_periods = {
            'today': RepairOrder.search_count([
                ('date_completed', '>=', today),
                ('date_completed', '<', today + timedelta(days=1))
            ]),
            'week': RepairOrder.search_count([
                ('date_completed', '>=', week_start),
                ('date_completed', '<=', today)
            ]),
            'month': RepairOrder.search_count([
                ('date_completed', '>=', month_start),
                ('date_completed', '<=', today)
            ])
        }
        
        # 2. Top 5 dispositivos más reparados
        device_data = RepairOrder.read_group(
            [('device_id', '!=', False)],
            ['device_brand', 'device_model'],
            ['device_brand', 'device_model'],
            limit=5
        )
        
        top_devices = []
        for item in device_data:
            brand = item['device_brand'] or 'Sin marca'
            model = item['device_model'] or 'Sin modelo'
            top_devices.append({
                'device': f"{brand} {model}",
                'count': item['__count']
            })
        
        # 3. Top técnicos con más reparaciones
        technician_data = RepairOrder.read_group(
            [('technician_id', '!=', False), ('state', 'in', ['ready', 'delivered'])],
            ['technician_id'],
            ['technician_id'],
            limit=5
        )
        
        top_technicians = []
        for item in technician_data:
            top_technicians.append({
                'technician': item['technician_id'][1],
                'count': item['technician_id_count']
            })
        
        return {
            'completed_periods': completed_periods,
            'top_devices': top_devices,
            'top_technicians': top_technicians
        }
    
    @api.model
    def get_chart_data(self):
        """Retorna datos para gráficos del dashboard"""
        RepairOrder = self.env['mobile.repair.order']
        
        # Datos por estado
        states_data = RepairOrder.read_group(
            [],
            ['state'],
            ['state']
        )
        
        # Datos por técnico (órdenes activas)
        technician_data = RepairOrder.read_group(
            [('state', 'in', ['draft', 'in_progress'])],
            ['technician_id'],
            ['technician_id']
        )
        
        # Actividad diaria (últimos 7 días)
        daily_data = []
        for i in range(7):
            date = fields.Date.today() - timedelta(days=i)
            count = RepairOrder.search_count([
                ('date_received', '>=', date),
                ('date_received', '<', date + timedelta(days=1))
            ])
            daily_data.append({
                'date': date.strftime('%d/%m'),
                'count': count
            })
        
        return {
            'states': {
                'labels': [self._get_state_label(item['state']) for item in states_data],
                'data': [item['state_count'] for item in states_data],
                'colors': [self._get_state_color(item['state']) for item in states_data]
            },
            'technicians': {
                'labels': [
                    item['technician_id'][1] if item['technician_id'] else 'Sin asignar'
                    for item in technician_data[:5]  # Top 5
                ],
                'data': [item['technician_id_count'] for item in technician_data[:5]]
            },
            'daily_activity': {
                'labels': [item['date'] for item in reversed(daily_data)],
                'data': [item['count'] for item in reversed(daily_data)]
            }
        }
    
    def _get_state_label(self, state):
        """Retorna etiqueta legible para el estado"""
        labels = {
            'draft': 'Recibidas',
            'in_progress': 'En Reparación',
            'ready': 'Listas',
            'delivered': 'Entregadas',
            'cancelled': 'Canceladas'
        }
        return labels.get(state, state)
    
    def _get_state_color(self, state):
        """Retorna color para el estado (paleta Odoo 18)"""
        colors = {
            'draft': '#6c757d',      # Gris - recibidas
            'in_progress': '#ffc107', # Amarillo - en proceso  
            'ready': '#28a745',      # Verde - listas
            'delivered': '#007bff',  # Azul - entregadas
            'cancelled': '#dc3545'   # Rojo - canceladas
        }
        return colors.get(state, '#6c757d')

    # ============================================================
    # ACCIONES RÁPIDAS
    # ============================================================
    
    def action_view_pending(self):
        """Ver órdenes pendientes"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes Pendientes',
            'res_model': 'mobile.repair.order',
            'view_mode': 'kanban,list,form',
            'domain': [('state', 'in', ['draft', 'in_progress'])],
            'context': {'search_default_group_by_state': 1}
        }
    
    def action_view_urgent(self):
        """Ver órdenes urgentes"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes Urgentes',
            'res_model': 'mobile.repair.order',
            'view_mode': 'kanban,list,form',
            'domain': [
                ('priority', '=', 'urgent'),
                ('state', 'in', ['draft', 'in_progress'])
            ]
        }
    
    def action_create_order(self):
        """Crear nueva orden"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Orden de Reparación',
            'res_model': 'mobile.repair.order',
            'view_mode': 'form',
            'context': {
                'default_priority': 'normal',
                'default_date_received': fields.Datetime.now()
            }
        }
    
    def action_refresh(self):
        """Actualizar datos del dashboard"""
        self._compute_kpis()
        self._compute_chart_kpis()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Dashboard Actualizado',
                'message': 'Los datos han sido actualizados correctamente.',
                'type': 'success',
                'sticky': False
            }
        }
    
    def action_view_monthly_analysis(self):
        """Ver análisis mensual detallado"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Análisis Mensual de Reparaciones',
            'res_model': 'mobile.repair.order',
            'view_mode': 'graph,pivot,list',
            'view_id': self.env.ref('mobile_repair_orders.view_repair_orders_graph_monthly').id,
            'context': {
                'search_default_filter_this_year': 1,
                'search_default_group_by_date_month': 1
            }
        }
    
    def action_view_technician_analysis(self):
        """Ver análisis por técnico"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Productividad por Técnico',
            'res_model': 'mobile.repair.order',
            'view_mode': 'graph,pivot,list',
            'view_id': self.env.ref('mobile_repair_orders.view_repair_orders_graph_technician').id,
            'context': {
                'search_default_filter_assigned': 1,
                'search_default_group_by_technician': 1
            }
        }
    
    def action_view_devices_analysis(self):
        """Ver análisis de dispositivos"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dispositivos Más Reparados',
            'res_model': 'mobile.repair.order',
            'view_mode': 'graph,pivot,list',
            'view_id': self.env.ref('mobile_repair_orders.view_repair_orders_graph_devices').id,
            'context': {
                'search_default_group_by_brand': 1
            }
        }