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
    display_name = fields.Char(string='Dispositivo', compute='_compute_display_name', store=True)
    fault_ids = fields.Many2many('mobile.fault', string='Fallas')

    @api.depends('brand_id', 'model_id')
    def _compute_display_name(self):
        for record in self:
            marca = record.brand_id.name if record.brand_id else ''
            modelo = record.model_id.name if record.model_id else ''
            partes = [p for p in [marca, modelo] if p]
            record.display_name = ' - '.join(partes)

class FaultCategory(models.Model):
    _name = 'mobile.fault.category'
    _description = 'Categoría de Fallas'

    name = fields.Char(string='Categoría', required=True)
    parent_id = fields.Many2one('mobile.fault.category', string='Categoría padre')
    child_ids = fields.One2many('mobile.fault.category', 'parent_id', string='Subcategorías')
    descripcion = fields.Text(string='Descripción')

class Fault(models.Model):
    _name = 'mobile.fault'
    _description = 'Falla de Dispositivo'

    name = fields.Char(string='Falla', required=True)
    category_id = fields.Many2one('mobile.fault.category', string='Categoría de Falla')
    descripcion = fields.Text(string='Descripción')

class MobileRepairConfig(models.TransientModel):
    _name = 'mobile.repair.config.settings'
    _inherit = 'res.config.settings'
    _description = 'Configuración de Reparaciones Móviles'
    # Puedes agregar aquí campos de configuración futura si lo requieres
    # Por ahora solo sirve como agrupador de menú