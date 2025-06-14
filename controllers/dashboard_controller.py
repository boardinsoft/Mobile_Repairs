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