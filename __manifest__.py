# -*- coding: utf-8 -*-
{
    'name': 'Mobile Repair Orders',
    'version': '1.0',
    'category': 'Services/Repair',
    'summary': 'Gestión de órdenes de reparación de dispositivos móviles',
    'description': """
        Módulo para la gestión de órdenes de reparación de dispositivos móviles.
        Incluye:
        * Gestión de marcas y modelos
        * Registro de dispositivos
        * Órdenes de reparación
        * Seguimiento de fallas y soluciones
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'mail',
        'repair',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mobile_device_data.xml',
        'views/mobile_brand_views.xml',
        'views/mobile_model_views.xml',
        'views/mobile_device_views.xml',
        'views/device_condition_views.xml',
        'views/fault_views.xml',
        'views/repair_solution_views.xml',
        'views/repair_order_views.xml',
        'views/repair_order_actions.xml',
        'views/repair_order_menu.xml',
        'views/dashboard_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}