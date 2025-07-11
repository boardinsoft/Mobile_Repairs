# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RepairDeviceBrand(models.Model):
    """Define una marca de dispositivo, como Apple o Samsung."""
    _name = 'mobile.repair.device.brand'
    _description = 'Marca de Dispositivo'
    _order = 'name'

    name = fields.Char(string='Marca', required=True, index=True)
    active = fields.Boolean(string='Activo', default=True)
    image = fields.Image(string='Logo', max_width=128, max_height=128)
    
    model_ids = fields.One2many(
        'mobile.repair.device.model', 'brand_id', string='Modelos'
    )
    model_count = fields.Integer(
        string='Cantidad de Modelos', compute='_compute_model_count'
    )
    
    @api.depends('model_ids')
    def _compute_model_count(self):
        for brand in self:
            brand.model_count = len(brand.model_ids)

class RepairDeviceModel(models.Model):
    """Define un modelo específico de dispositivo, como 'iPhone 15'."""
    _name = 'mobile.repair.device.model'
    _description = 'Modelo de Dispositivo'
    _order = 'brand_id, name'
    _rec_name = 'display_name'

    name = fields.Char(string='Modelo', required=True, index=True)
    brand_id = fields.Many2one(
        'mobile.repair.device.brand', string='Marca', required=True, ondelete='cascade'
    )
    active = fields.Boolean(string='Activo', default=True)
    
    # Información técnica
    release_year = fields.Integer(string='Año de Lanzamiento')
    screen_size = fields.Float(string='Tamaño Pantalla (pulgadas)', digits='Product Unit of Measure')
    operating_system = fields.Selection([
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('other', 'Otro')
    ], string='Sistema Operativo')
    
    display_name = fields.Char(
        string='Nombre Completo', compute='_compute_display_name', store=True, readonly=True
    )
    
    @api.depends('brand_id.name', 'name')
    def _compute_display_name(self):
        for model in self:
            if model.brand_id:
                model.display_name = f"{model.brand_id.name} {model.name}"
            else:
                model.display_name = model.name

class RepairDeviceColor(models.Model):
    """Define un color para un dispositivo."""
    _name = 'mobile.repair.device.color'
    _description = 'Color de Dispositivo'
    _order = 'name'

    name = fields.Char(string='Color', required=True, index=True)
    active = fields.Boolean(string='Activo', default=True)
    color_code = fields.Char(
        string='Código de Color', help='Código hexadecimal del color.', default='#6c757d'
    )

class RepairDeviceAccessory(models.Model):
    """Define un accesorio que puede venir con un dispositivo."""
    _name = 'mobile.repair.device.accessory'
    _description = 'Accesorio de Dispositivo'
    _order = 'name'

    name = fields.Char(string='Accesorio', required=True, index=True)
    active = fields.Boolean(string='Activo', default=True)
    accessory_type = fields.Selection([
        ('tapa', 'Tapa'),
        ('sim', 'SIM'),
        ('sd_card', 'Memoria SD'),
        ('sim_tray', 'Bandeja SIM')
    ], string='Tipo', default='tapa')
    
    color_code = fields.Char(
        string='Código de Color', compute='_compute_color_code', store=True
    )
    
    @api.depends('accessory_type')
    def _compute_color_code(self):
        """Asigna colores basados en el tipo de accesorio para una mejor UX."""
        color_map = {'tapa': '#6f42c1', 'sim': '#28a745', 'sd_card': '#fd7e14', 'sim_tray': '#17a2b8'}
        for accessory in self:
            accessory.color_code = color_map.get(accessory.accessory_type, '#6c757d')

class RepairDevice(models.Model):
    """Representa un dispositivo físico único de un cliente."""
    _name = 'mobile.repair.device'
    _description = 'Dispositivo Individual'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    # Relaciones principales
    brand_id = fields.Many2one('mobile.repair.device.brand', string='Marca', required=True, index=True)
    model_id = fields.Many2one(
        'mobile.repair.device.model', string='Modelo',
        domain="[('brand_id','=',brand_id)]", required=True, index=True
    )
    
    # Información del dispositivo
    imei = fields.Char(string='IMEI/Serial', index=True, help="Número único de identificación del dispositivo.")
    device_code = fields.Char(
        string='Código', required=True, index=True, copy=False, readonly=True,
        help="Código único generado automáticamente."
    )
    color_ids = fields.Many2many('mobile.repair.device.color', string='Colores')
    
    # Estado funcional y físico
    powers_on = fields.Boolean(string='Enciende', default=True, help="¿El dispositivo enciende correctamente?")
    physical_state = fields.Selection([
        ('screen_broken', 'Pantalla Rota'), ('scratches', 'Rayaduras'),
        ('dents', 'Golpes'), ('screen_lines', 'Líneas en Pantalla'),
        ('good', 'Buen Estado')],
        string='Estado Físico', default='good', required=True
    )
    
    # Información de seguridad
    lock_type = fields.Selection([
        ('none', 'Sin bloqueo'), ('password', 'Contraseña'),
        ('pin', 'PIN'), ('pattern', 'Patrón')],
        string='Tipo de bloqueo', default='none'
    )
    lock_code = fields.Char(string='Código de Bloqueo', help="Código de desbloqueo del dispositivo.")
    
    # Accesorios y Notas
    accessory_ids = fields.Many2many('mobile.repair.device.accessory', string='Accesorios Incluidos')
    notes = fields.Text(string='Observaciones')
    
    display_name = fields.Char(string='Nombre del Dispositivo', compute='_compute_display_name', store=True, readonly=True)
    
    # Relación con órdenes de reparación
    repair_ids = fields.One2many('mobile.repair.order', 'device_id', string='Órdenes de Reparación')
    
    # Estadísticas
    repair_count = fields.Integer(string='Reparaciones', compute='_compute_repair_stats', store=True, readonly=True)
    last_repair_date = fields.Datetime(string='Última Reparación', compute='_compute_repair_stats', store=True, readonly=True)
    
    @api.depends('brand_id.name', 'model_id.name', 'color_ids.name', 'device_code')
    def _compute_display_name(self):
        for device in self:
            parts = [f"[{device.device_code}]"] if device.device_code else []
            if device.brand_id and device.model_id:
                parts.append(f"{device.brand_id.name} {device.model_id.name}")
            if device.color_ids:
                parts.append(", ".join(device.color_ids.mapped('name')))
            device.display_name = " - ".join(parts) if parts else "Dispositivo sin definir"
    
    @api.depends('repair_ids')
    def _compute_repair_stats(self):
        """Calcula estadísticas de reparaciones de forma optimizada."""
        for device in self:
            device.repair_count = len(device.repair_ids)
            if device.repair_ids:
                device.last_repair_date = max(device.repair_ids.mapped('date_received'))
            else:
                device.last_repair_date = False
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'device_code' not in vals or not vals['device_code']:
                vals['device_code'] = self.env['ir.sequence'].next_by_code('mobile.repair.device') or 'Nuevo'
        return super().create(vals_list)
    
    @api.constrains('imei')
    def _check_imei_unique(self):
        for device in self:
            if device.imei:
                if not device.imei.isdigit() or len(device.imei) != 15:
                    raise ValidationError("El IMEI debe contener exactamente 15 dígitos numéricos.")
                if self.search_count([('imei', '=', device.imei), ('id', '!=', device.id)]) > 0:
                    raise ValidationError(f"Ya existe un dispositivo con IMEI {device.imei}")
    
    @api.constrains('lock_type', 'lock_code')
    def _check_lock_code_format(self):
        for device in self:
            if device.lock_type == 'pin' and device.lock_code:
                if not device.lock_code.isdigit():
                    raise ValidationError("El PIN debe contener solo números.")
            elif device.lock_type == 'password' and device.lock_code:
                if not device.lock_code.isalnum():
                    raise ValidationError("La contraseña debe ser alfanumérica.")

    def action_view_repairs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Reparaciones de {self.display_name}',
            'res_model': 'mobile.repair.order',
            'view_mode': 'list,kanban,form',
            'domain': [('device_id', '=', self.id)],
            'context': {'default_device_id': self.id}
        }