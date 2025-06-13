# -*- coding: utf-8 -*-
{
    'name': 'Mobile Repair Orders',
    'version': '1.0',
    'category': 'Services/Repair',
    'summary': 'Gestión de órdenes de reparación de dispositivos móviles',
    'description': """
        Módulo para la gestión integral de órdenes de reparación de dispositivos móviles.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'mail',
        'repair',
    ],
    'data': [
        # Seguridad y secuencias (siempre primero)
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mobile_device_data.xml',

        # Vistas de catálogos
        # (Las vistas de marcas y modelos están incluidas dentro de mobile_device_views.xml)
        'views/mobile_device_views.xml',
        'views/device_condition_views.xml',
        'views/fault_views.xml',
        'views/fault_config_views.xml',
        'views/repair_solution_views.xml',
        'views/repair_line_views.xml',

        # Vistas principales de negocio
        'views/repair_order_views.xml',

        # Acciones y menús
        'views/repair_order_actions.xml',
        'views/repair_order_filtered_actions.xml',
        'views/repair_order_menu.xml',

        # Plantillas y dashboard
        'views/repair_order_templates.xml',
        'views/dashboard_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}