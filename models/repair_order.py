from odoo import models, fields, api

class RepairOrder(models.Model):
    _name = 'mobile.repair.order'
    _description = 'Repair Order'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: self.env['ir.sequence'].next_by_code('mobile_repair_order'))
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    device_id = fields.Many2one('mobile.device', string='Device', required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ], string='Status', default='draft')
    technician_id = fields.Many2one('res.users', string='Technician')
    repair_date = fields.Datetime(string='Repair Date', default=fields.Datetime.now)
    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('mobile_repair_order')
        return super(RepairOrder, self).create(vals)

    def action_complete(self):
        self.status = 'completed'

    def action_cancel(self):
        self.status = 'canceled'

    def action_save(self):
        # Método dummy para el botón Save
        return True