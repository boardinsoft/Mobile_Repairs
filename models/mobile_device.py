from odoo import models, fields

class MobileDevice(models.Model):
    _name = 'mobile.device'
    _description = 'Mobile Device'

    name = fields.Char(string='Device Name', required=True)
    brand = fields.Char(string='Brand', required=True)
    model = fields.Char(string='Model', required=True)
    owner_id = fields.Many2one('res.partner', string='Owner')