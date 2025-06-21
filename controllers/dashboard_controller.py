# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json

class RepairDashboardController(http.Controller):
    """Controlador para el dashboard de reparaciones - optimizado para Odoo 18"""

    @http.route('/repair/dashboard/chart_data', type='json', auth='user')
    def get_chart_data(self):
        """Retorna datos para los gráficos del dashboard"""
        try:
            RepairOrder = request.env['mobile.repair.order']
            
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
            
            # Datos de actividad diaria (últimos 7 días)
            from datetime import datetime, timedelta
            daily_data = []
            for i in range(7):
                date = datetime.now().date() - timedelta(days=i)
                count = RepairOrder.search_count([
                    ('date_received', '>=', f"{date} 00:00:00"),
                    ('date_received', '<=', f"{date} 23:59:59")
                ])
                daily_data.append({
                    'date': date.strftime('%d/%m'),
                    'count': count
                })
            
            # Preparar datos para gráficos
            chart_data = {
                'states_chart': {
                    'labels': [self._get_state_label(item['state']) for item in states_data],
                    'data': [item['state_count'] for item in states_data],
                    'backgroundColor': [self._get_state_color(item['state']) for item in states_data]
                },
                'technicians_chart': {
                    'labels': [
                        item['technician_id'][1] if item['technician_id'] else 'Sin asignar'
                        for item in technician_data[:5]  # Top 5
                    ],
                    'data': [item['technician_id_count'] for item in technician_data[:5]],
                    'backgroundColor': '#007bff'
                },
                'daily_activity': {
                    'labels': [item['date'] for item in reversed(daily_data)],
                    'data': [item['count'] for item in reversed(daily_data)],
                    'backgroundColor': '#28a745',
                    'borderColor': '#20c997'
                }
            }
            
            return chart_data
            
        except Exception as e:
            # Log del error para debug
            request.env['ir.logging'].sudo().create({
                'name': 'Dashboard Chart Error',
                'type': 'server',
                'level': 'ERROR',
                'message': str(e),
                'path': 'mobile_repair_orders.dashboard',
                'func': 'get_chart_data'
            })
            
            # Retornar datos vacíos en caso de error
            return {
                'states_chart': {'labels': [], 'data': [], 'backgroundColor': []},
                'technicians_chart': {'labels': [], 'data': [], 'backgroundColor': '#007bff'},
                'daily_activity': {'labels': [], 'data': [], 'backgroundColor': '#28a745'}
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

    @http.route('/repair/dashboard/kpis', type='json', auth='user')
    def get_kpis_data(self):
        """Retorna KPIs para el dashboard"""
        try:
            RepairOrder = request.env['mobile.repair.order']
            from datetime import datetime, timedelta
            
            # Fecha actual y primer día del mes
            today = datetime.now().date()
            first_day_month = today.replace(day=1)
            
            # KPIs básicos
            total_orders = RepairOrder.search_count([])
            pending_orders = RepairOrder.search_count([
                ('state', 'in', ['draft', 'in_progress'])
            ])
            completed_today = RepairOrder.search_count([
                ('date_completed', '>=', f"{today} 00:00:00"),
                ('date_completed', '<=', f"{today} 23:59:59")
            ])
            urgent_orders = RepairOrder.search_count([
                ('priority', '=', 'urgent'),
                ('state', 'in', ['draft', 'in_progress'])
            ])
            
            # Ingresos del mes
            completed_orders = RepairOrder.search([
                ('date_completed', '>=', first_day_month),
                ('state', 'in', ['ready', 'delivered']),
                ('final_cost', '>', 0)
            ])
            revenue_month = sum(completed_orders.mapped('final_cost'))
            
            # Duración promedio
            finished_orders = RepairOrder.search([
                ('date_completed', '!=', False),
                ('duration_days', '>', 0)
            ])
            avg_duration = 0
            if finished_orders:
                avg_duration = sum(finished_orders.mapped('duration_days')) / len(finished_orders)
            
            # Técnico más productivo
            top_technician = self._get_top_technician_kpi()
            
            return {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'completed_today': completed_today,
                'urgent_orders': urgent_orders,
                'revenue_month': revenue_month,
                'avg_duration': round(avg_duration, 1),
                'top_technician': top_technician
            }
            
        except Exception as e:
            return {
                'total_orders': 0,
                'pending_orders': 0,
                'completed_today': 0,
                'urgent_orders': 0,
                'revenue_month': 0,
                'avg_duration': 0,
                'top_technician': 'Sin datos'
            }

    def _get_top_technician_kpi(self):
        """Obtiene el técnico más productivo del mes"""
        try:
            RepairOrder = request.env['mobile.repair.order']
            from datetime import datetime
            
            first_day_month = datetime.now().date().replace(day=1)
            
            technician_data = RepairOrder.read_group(
                [
                    ('date_completed', '>=', first_day_month),
                    ('technician_id', '!=', False),
                    ('state', 'in', ['ready', 'delivered'])
                ],
                ['technician_id'],
                ['technician_id']
            )
            
            if technician_data:
                top = max(technician_data, key=lambda x: x['technician_id_count'])
                return f"{top['technician_id'][1]} ({top['technician_id_count']})"
            
            return "Sin datos"
            
        except:
            return "Sin datos"