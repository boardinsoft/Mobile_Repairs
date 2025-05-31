from odoo import models, fields, api

class MobileBrand(models.Model):
    _name = 'mobile.brand'
    _description = 'Marca de dispositivo móvil'

    name = fields.Char(string='Marca', required=True)
    descripcion = fields.Text(string='Descripción')
    model_ids = fields.One2many('mobile.model', 'brand_id', string='Modelos')

class MobileModel(models.Model):
    _name = 'mobile.model'
    _description = 'Modelo de dispositivo móvil'

    name = fields.Char(string='Modelo', required=True)
    brand_id = fields.Many2one('mobile.brand', string='Marca', required=True)
    descripcion = fields.Text(string='Descripción')

class MobileDevice(models.Model):
    _name = 'mobile.device'
    _description = 'Dispositivo Móvil'

    brand_id = fields.Many2one('mobile.brand', string='Marca', required=True)
    model_id = fields.Many2one(
        'mobile.model',
        string='Modelo',
        required=True,
        domain="[('brand_id', '=', brand_id)]"
    )
    imei = fields.Char(string='IMEI')
    serial_number = fields.Char(string='Número de serie')
    color = fields.Char(string='Color')
    enciende = fields.Boolean(string='¿Enciende?')
    garantia = fields.Boolean(string='En garantía')
    descripcion = fields.Text(string='Descripción adicional')
    owner_id = fields.Many2one('res.partner', string='Propietario')
    display_name = fields.Char(string='Dispositivo', compute='_compute_display_name', store=True)

    @api.depends('brand_id', 'model_id')
    def _compute_display_name(self):
        for record in self:
            marca = record.brand_id.name if record.brand_id else ''
            modelo = record.model_id.name if record.model_id else ''
            partes = [p for p in [marca, modelo] if p]
            record.display_name = ' - '.join(partes)