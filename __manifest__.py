# -*- coding: utf-8 -*-
{
    'name': 'Mobile Repair Orders',
    'summary': 'Manage mobile phone repair orders and invoicing.',
    'description': """
        This module helps in managing the complete lifecycle of mobile phone repairs,
        from receiving the device to invoicing the customer. Track devices, repairs,
        parts used, technicians, and generate invoices for completed services.
    """,
    'author': 'Gabriel Gutierrez',
    'website': 'http://www.boardinsoft.com',
    'category': 'Services/Repair',
    'version': '1.0.0',
    'sequence': 10,
    'depends': [
        'base',
        'contacts',
        'mail',
        'product',
        'sale_management',
        'account',
        'stock',
    ],
    'data': [
        # Seguridad (primero)
        'security/mobile_repair_orders_security.xml',    # ← CORREGIDO: Usar el nombre real del archivo
        'security/ir.model.access.csv',
        
        # Datos maestros y secuencias
        'data/ir_sequence_data.xml',
        
        # Acciones (antes que los menús)
        'views/repair_order_actions.xml',
        
        # Vistas de modelos
        'views/brand_model_views.xml',
        'views/device_condition_views.xml',
        'views/fault_config_views.xml',
        'views/mobile_device_views.xml',
        'views/repair_line_views.xml',
        'views/repair_order_views.xml',
        
        # Menú principal (después de las acciones)
        'views/repair_order_menu.xml',
        
        # Plantillas y reportes
        #'views/repair_order_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}