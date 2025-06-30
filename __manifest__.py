# -*- coding: utf-8 -*-
{
    'name': 'Mobile Repair Orders',
    'version': '2.0.1',
    'category': 'Services',
    'summary': 'Gestión minimalista de reparaciones móviles',
    'description': """
        Módulo optimizado para la gestión eficiente de reparaciones de dispositivos móviles.
        
        Características principales:
        • Flujo de trabajo simplificado
        • Interfaz minimalista y rápida
        • Gestión completa del ciclo de reparación
        • Reportes y análisis integrados
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'mail',
        'web',
        'stock',
        'sale_stock',
        'sale_management',
        'account',
    ],
    'data': [
        'views/device_views.xml',
        # Seguridad
        'security/ir.model.access.csv',
        
        # Datos base
        'data/sequences.xml',
        'data/base_data.xml',
        
        # Vistas principales
        'views/repair_order_views.xml',
        'views/repair_problem_views.xml',
        'views/devices.xml',
        'views/repair_analytics_views.xml',
        'views/menus.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}