# -*- coding: utf-8 -*-
{
    'name': 'Mobile Repair Orders',
    'version': '1.0.0',
    'category': 'Services',
    'summary': 'Gestión completa de reparaciones móviles con integración de ventas',
    'description': """
        Módulo optimizado para la gestión eficiente de reparaciones de dispositivos móviles.
        
        Características principales:
        • Flujo de trabajo con estados: Borrador → En reparación → Reparado → Entregado
        • Líneas de presupuesto heredadas del módulo de ventas
        • Interfaz minimalista y rápida
        • Gestión completa del ciclo de reparación
        • Integración con inventario y facturación
        • Reportes y análisis integrados
        
        Estados del flujo:
        - Borrador: Orden recién creada
        - En reparación: Técnico trabajando en el dispositivo
        - Reparado: Reparación completada, listo para entrega
        - Entregado: Dispositivo entregado al cliente
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
        # Seguridad (se carga primero)
        'security/mobile_repair_orders_security.xml',
        'security/ir.model.access.csv',
        
        # Datos base
        'data/sequences.xml',
        
        # Vistas (en orden lógico)
        'views/device_views.xml',
        'views/repair_problem_views.xml',
        'views/repair_order_views.xml',
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
    'images': ['static/description/banner.png'],
}