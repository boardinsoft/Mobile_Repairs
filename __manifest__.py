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
    'category': 'Servicios/Reparaciones',
    'version': '1.0.0',
    'depends': [
        'base',
        'account',
        'stock',
        'contacts',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/mobile_repair_orders_security.xml',
        'views/repair_order_views.xml',
        'views/mobile_device_views.xml',
        'views/repair_order_menu.xml',
        'views/repair_order_templates.xml',
        'data/ir_sequence_data.xml',
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}