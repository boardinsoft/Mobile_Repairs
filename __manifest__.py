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
        'mail',  # Para el chatter
    ],
    'data': [
        # Primero: Seguridad y datos maestros
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        
        # Segundo: Vistas (que contienen las acciones)
        'views/fault_config_views.xml',
        'views/brand_model_views.xml',  # Nuevo archivo
        'views/mobile_device_views.xml',     
        'views/repair_order_views.xml',
        
        # Tercero: Menús (que referencian las acciones)
        'views/repair_order_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}