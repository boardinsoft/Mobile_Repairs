# -*- coding: utf-8 -*-
{
    'name': 'Mobile Repair Orders',
    'version': '2.0.1',
    'category': 'Services',
    'summary': 'Gestión minimalista de reparaciones móviles',
    'description': """
        Módulo optimizado para la gestión eficiente de reparaciones de dispositivos móviles.
        
        Características principales:
        • Dashboard visual con métricas clave
        • Flujo de trabajo simplificado
        • Interfaz minimalista y rápida
        • Gestión completa del ciclo de reparación
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        
        # Datos base
        'data/sequences.xml',
        'data/base_data.xml',
        
        # Vistas principales
        'views/repair_order_views.xml',
        'views/devices.xml',
        'views/dashboard.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mobile_repair_orders/static/src/scss/repair_dashboard.scss',
            'mobile_repair_orders/static/src/scss/kanban_clean.scss',
            'mobile_repair_orders/static/src/components/dashboard/dashboard.js',
            'mobile_repair_orders/static/src/components/dashboard/dashboard.xml',
            'mobile_repair_orders/static/src/components/dashboard/dashboard_widget.js',
            'mobile_repair_orders/static/src/components/devices/devices.js',
            'mobile_repair_orders/static/src/components/devices/devices.xml',
        ],
    },
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}