from odoo import http, fields
from odoo.http import request

class MobileRepairDashboardController(http.Controller):
    @http.route('/mobile_repair_orders/dashboard/bars', type='json', auth='user')
    def get_bar_data(self):
        env = request.env
        # Agrupar órdenes por estado
        data = env['mobile.repair.order'].read_group(
            [],
            ['id'],
            ['status']
        )
        labels = []
        counts = []
        for rec in data:
            labels.append(rec['status'])
            counts.append(rec['status_count'])
        return {
            'labels': labels,
            'datasets': [{
                'data': counts,
                'backgroundColor': '#875A7B'
            }]
        } 