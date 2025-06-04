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
        # ================================
        # 1. SEGURIDAD (SIEMPRE PRIMERO)
        # ================================
        'security/mobile_repair_orders_security.xml',
        'security/ir.model.access.csv',
        
        # ================================
        # 2. DATOS MAESTROS Y SECUENCIAS
        # ================================
        'data/ir_sequence_data.xml',
        
        # ================================
        # 3. VISTAS DE MODELOS BÁSICOS
        # ================================
        # Configuración básica de marcas, modelos y condiciones
        'views/brand_model_views.xml',
        'views/device_condition_views.xml',
        'views/fault_config_views.xml',
        
        # Vistas de dispositivos móviles
        'views/mobile_device_views.xml',
        
        # ================================
        # 4. VISTAS DE ÓRDENES DE REPARACIÓN
        # ================================
        'views/repair_line_views.xml',
        'views/repair_order_views.xml',
        
        # ================================
        # 5. DASHBOARD E INFORMACIÓN GENERAL
        # ================================
        'views/dashboard_view.xml',
        
        # ================================
        # 6. ACCIONES (ANTES QUE LOS MENÚS)
        # ================================
        'views/repair_order_actions.xml',
        'views/repair_order_filtered_actions.xml',
        
        # ================================
        # 7. MENÚS (SIEMPRE AL FINAL)
        # ================================
        'views/repair_order_menu.xml',
        
        # ================================
        # 8. PLANTILLAS Y REPORTES (OPCIONAL)
        # ================================
        # 'views/repair_order_templates.xml',
        # 'reports/repair_order_reports.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}