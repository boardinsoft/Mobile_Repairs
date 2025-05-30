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
        #'account',
        #'stock',
        'contacts',
        #'product',
    ],
    'data': [
        # Primero: Datos maestros y configuraciones
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        
        # Segundo: Vistas que contienen las acciones
        'views/repair_order_views.xml',      # Contiene action_repair_order_form_view
        'views/mobile_device_views.xml',     # Contiene action_mobile_device
        'views/repair_order_templates.xml',  # Plantillas adicionales
        
        # Tercero: Menús que referencian las acciones (siempre al final)
        'views/repair_order_menu.xml',       # Referencias: action_repair_order_form_view y action_mobile_device
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}