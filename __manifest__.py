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
<<<<<<< HEAD
        # Seguridad (SIEMPRE PRIMERO)
        'security/mobile_repair_orders_security.xml',
        'security/ir.model.access.csv',
        
        # Datos base y configuración
        'data/repair_sequence.xml',
        
        # Vistas principales
=======
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mobile_device_data.xml',
        'views/mobile_brand_views.xml',
        'views/mobile_model_views.xml',
        'views/mobile_device_views.xml',
        'views/device_condition_views.xml',
        'views/fault_views.xml',
        'views/repair_solution_views.xml',
>>>>>>> Develop
        'views/repair_order_views.xml',
        'views/repair_order_actions.xml',
        'views/repair_order_menu.xml',
        'views/dashboard_views.xml',
    ],
<<<<<<< HEAD
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mobile_repair_orders/static/src/css/dashboard.css',
        ],
    },
    'images': [
        #'static/description/banner.png',
        #'static/description/icon.png',
    ],
=======
    'demo': [],
>>>>>>> Develop
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}