from odoo import models, fields, api

class RepairOrder(models.Model):
    _name = 'mobile.repair.order'
    _description = 'Repair Order'

    name = fields.Char(string='Referencia de Orden', required=True, copy=False, readonly=True, index=True, default=lambda self: self.env['ir.sequence'].next_by_code('mobile_repair_order'))
    customer_id = fields.Many2one('res.partner', string='Cliente', required=True)
    device_id = fields.Many2one('mobile.device', string='Dispositivo', required=True)
    status = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completada'),
        ('canceled', 'Cancelada'),
    ], string='Estado', default='draft')
    technician_id = fields.Many2one('res.users', string='Técnico')
    repair_date = fields.Datetime(string='Fecha de reparación', default=fields.Datetime.now)
    notes = fields.Text(string='Notas')

    @api.model
    def create(self, vals_list): # Ahora esperamos una lista de diccionarios
        # Aseguramos que vals_list siempre sea una lista, incluso si se pasa un solo diccionario
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        # Preprocesar los valores antes de la creación en lote
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('mobile_repair_order')

        # Llamar al super método para la creación en lote
        # Odoo base manejará la inserción eficiente en la base de datos
        return super(RepairOrder, self).create(vals_list)

    def action_complete(self):
        self.status = 'completed'

    def action_cancel(self):
        self.status = 'canceled'

    def action_save(self):
        # Método dummy para el botón Save
        return True