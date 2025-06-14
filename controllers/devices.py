# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class DeviceController(http.Controller):
    """Controlador para datos de dispositivos y clientes"""

    @http.route('/repair/customer/<int:customer_id>/stats', type='json', auth='user')
    def get_customer_stats(self, customer_id):
        """Obtiene estadísticas de reparaciones de un cliente específico"""
        try:
            RepairOrder = request.env['mobile.repair.order']
            
            # Estadísticas básicas
            total_repairs = RepairOrder.search_count([
                ('customer_id', '=', customer_id)
            ])
            
            completed_repairs = RepairOrder.search_count([
                ('customer_id', '=', customer_id),
                ('state', 'in', ['ready', 'delivered'])
            ])
            
            pending_repairs = RepairOrder.search_count([
                ('customer_id', '=', customer_id),
                ('state', 'in', ['draft', 'in_progress'])
            ])
            
            # Últimas 5 reparaciones
            recent_orders = RepairOrder.search([
                ('customer_id', '=', customer_id)
            ], order='date_received desc', limit=5)
            
            recent_repairs = []
            for order in recent_orders:
                recent_repairs.append({
                    'id': order.id,
                    'name': order.name,
                    'device_info': order.device_info,
                    'state': order.state,
                    'state_label': dict(order._fields['state'].selection)[order.state],
                    'date_received': order.date_received.strftime('%d/%m/%Y') if order.date_received else '',
                    'problem_description': order.problem_description[:100] + '...' if len(order.problem_description) > 100 else order.problem_description
                })
            
            return {
                'total_repairs': total_repairs,
                'completed_repairs': completed_repairs,
                'pending_repairs': pending_repairs,
                'recent_repairs': recent_repairs
            }
            
        except Exception as e:
            return {
                'total_repairs': 0,
                'completed_repairs': 0,
                'pending_repairs': 0,
                'recent_repairs': []
            }

    @http.route('/repair/customer/<int:customer_id>/recent_repairs', type='json', auth='user')
    def get_recent_repairs_html(self, customer_id):
        """Genera HTML para mostrar las reparaciones recientes"""
        try:
            RepairOrder = request.env['mobile.repair.order']
            
            recent_orders = RepairOrder.search([
                ('customer_id', '=', customer_id)
            ], order='date_received desc', limit=5)
            
            if not recent_orders:
                return {
                    'html': '''
                        <div class="text-center text-muted py-4">
                            <i class="fa fa-mobile fa-3x mb-3 opacity-25"></i>
                            <p class="mb-0">No hay reparaciones registradas</p>
                            <small>Las reparaciones aparecerán aquí cuando se registren</small>
                        </div>
                    '''
                }
            
            html_parts = []
            for order in recent_orders:
                state_colors = {
                    'draft': 'secondary',
                    'in_progress': 'warning',
                    'ready': 'success',
                    'delivered': 'primary',
                    'cancelled': 'danger'
                }
                
                state_icons = {
                    'draft': '📥',
                    'in_progress': '🔧',
                    'ready': '✅',
                    'delivered': '📦',
                    'cancelled': '❌'
                }
                
                state_labels = {
                    'draft': 'Recibida',
                    'in_progress': 'En Reparación',
                    'ready': 'Lista',
                    'delivered': 'Entregada',
                    'cancelled': 'Cancelada'
                }
                
                color = state_colors.get(order.state, 'secondary')
                icon = state_icons.get(order.state, '📱')
                label = state_labels.get(order.state, order.state)
                
                html_parts.append(f'''
                    <div class="card mb-3 border-{color}">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <h6 class="card-title mb-1">
                                        {icon} {order.name}
                                        <span class="badge badge-{color} ms-2">{label}</span>
                                    </h6>
                                    <p class="card-text">
                                        <strong>📱 {order.device_info}</strong><br/>
                                        <small class="text-muted">
                                            📅 {order.date_received.strftime('%d/%m/%Y %H:%M') if order.date_received else 'Sin fecha'}
                                        </small>
                                    </p>
                                    <p class="card-text">
                                        <small>{order.problem_description[:80]}{'...' if len(order.problem_description) > 80 else ''}</small>
                                    </p>
                                </div>
                                <div class="text-end">
                                    <button class="btn btn-outline-primary btn-sm" 
                                            onclick="window.open('/web#id={order.id}&model=mobile.repair.order&view_type=form', '_blank')">
                                        Ver Detalle
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                ''')
            
            return {
                'html': ''.join(html_parts)
            }
            
        except Exception as e:
            return {
                'html': f'''
                    <div class="alert alert-warning" role="alert">
                        <strong>Error:</strong> No se pudieron cargar las reparaciones.
                        <br/><small>{str(e)}</small>
                    </div>
                '''
            }