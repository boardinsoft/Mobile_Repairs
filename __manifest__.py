# -*- coding: utf-8 -*-
{
    'name': 'Mobile Repair Orders',
    'summary': 'Comprehensive mobile phone repair management system.',
    'description': """
        🔧 Sistema Completo de Gestión de Reparaciones Móviles
        =====================================================
        
        Este módulo proporciona una solución integral para la gestión del ciclo completo 
        de reparaciones de dispositivos móviles, desde la recepción del equipo hasta la 
        facturación al cliente.
        
        📊 Características Principales:
        • Dashboard interactivo con KPIs en tiempo real
        • Gestión completa de órdenes de reparación
        • Catálogo de dispositivos, marcas y modelos
        • Sistema de diagnósticos y clasificación de fallas
        • Seguimiento de estados y procesos
        • Navegación organizada por módulos
        • Reportes y análisis de rendimiento
        
        🚀 Beneficios:
        • Incrementa la eficiencia operacional
        • Mejora el control de inventario
        • Facilita el seguimiento de servicios
        • Optimiza los tiempos de reparación
        • Proporciona insights de negocio
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
        'web',
    ],
    'data': [
        # Seguridad (SIEMPRE PRIMERO)
        #'security/mobile_repair_orders_security.xml',
        'security/ir.model.access.csv',
        
        
        # Datos base y configuración
        'data/repair_sequence.xml',
        
        # Vistas principales
        'views/repair_order_views.xml',
        'views/dashboard_view.xml',
        
        # Acciones (antes de menús)
        'views/repair_order_complete_actions.xml',
        
        # Menús (AL FINAL)
        'views/repair_order_menu.xml',
    ],
    'demo': [
        #'demo/demo_data.xml',
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
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'price': 299.00,
    'currency': 'USD',
}