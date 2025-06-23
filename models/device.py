# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RepairDeviceBrand(models.Model):
    """Marcas de dispositivos optimizado"""
    _name = 'mobile_repair.device.brand'
    _description = 'Marca de Dispositivo'
    _order = 'name'

    name = fields.Char(string='Marca', required=True, index=True)
    active = fields.Boolean(string='Activo', default=True)
    image = fields.Image(string='Logo', max_width=128, max_height=128)
    
    # Campos computados
    model_count = fields.Integer(
        string='Modelos', 
        compute='_compute_model_count'
    )
    
    @api.depends('name')
    def _compute_model_count(self):
        for brand in self:
            brand.model_count = self.env['mobile_repair.device.model'].search_count([
                ('brand_id', '=', brand.id)
            ])

class RepairDeviceModel(models.Model):
    """Modelos de dispositivos optimizado"""
    _name = 'mobile_repair.device.model'
    _description = 'Modelo de Dispositivo'
    _order = 'brand_id, name'

    name = fields.Char(string='Modelo', required=True, index=True)
    brand_id = fields.Many2one(
        'mobile_repair.device.brand', 
        string='Marca', 
        required=True,
        ondelete='cascade'
    )
    active = fields.Boolean(string='Activo', default=True)
    
    # Información técnica
    release_year = fields.Integer(string='Año de Lanzamiento')
    screen_size = fields.Float(string='Tamaño Pantalla (pulgadas)', digits=(3,1))
    operating_system = fields.Selection([
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('other', 'Otro')
    ], string='Sistema Operativo')
    
    # Campo combinado para mostrar
    display_name = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('brand_id.name', 'name')
    def _compute_display_name(self):
        for model in self:
            if model.brand_id:
                model.display_name = f"{model.brand_id.name} {model.name}"
            else:
                model.display_name = model.name

class RepairDeviceColor(models.Model):
    """Colores de dispositivos con etiquetas de color"""
    _name = 'mobile_repair.device.color'
    _description = 'Color de Dispositivo'
    _order = 'name'

    name = fields.Char(string='Color', required=True, index=True)
    active = fields.Boolean(string='Activo', default=True)
    color_code = fields.Char(
        string='Código de Color',
        help='Código hexadecimal del color para mostrar en la etiqueta',
        default='#6c757d'
    )

class RepairDeviceAccessory(models.Model):
    """Accesorios de dispositivos optimizado con colores"""
    _name = 'mobile_repair.device.accessory'
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
        string='Código de Color',
        help='Código hexadecimal del color para mostrar en la etiqueta',
        compute='_compute_color_code',
        store=True
    )
    
    @api.depends('accessory_type')
    def _compute_color_code(self):
        """Asigna colores basados en el tipo de accesorio"""
        color_map = {
            'tapa': '#6f42c1',     # Púrpura
            'sim': '#28a745',      # Verde
            'sd_card': '#fd7e14',  # Naranja
            'sim_tray': '#17a2b8'  # Azul claro
        }
        for accessory in self:
            accessory.color_code = color_map.get(accessory.accessory_type, '#6c757d')

class RepairDevice(models.Model):
    """Dispositivo individual optimizado con relaciones mejoradas"""
    _name = 'mobile_repair.device'
    _description = 'Dispositivo Individual'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    # Relaciones principales
    brand_id = fields.Many2one(
        'mobile_repair.device.brand', 
        string='Marca', 
        required=True,
        index=True
    )
    model_id = fields.Many2one(
        'mobile_repair.device.model', 
        string='Modelo',
        domain="[('brand_id','=',brand_id)]", 
        required=True,
        index=True
    )
    
    # Información del dispositivo
    imei = fields.Char(
        string='IMEI/Serial', 
        index=True,
        help="Número único de identificación del dispositivo (opcional)"
    )
    
    # Código único con secuencia automática
    device_code = fields.Char(
        string='Código',
        required=True,
        index=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('mobile_repair.device') or 'DEV001',
        help="Código único generado automáticamente"
    )
    
    color_ids = fields.Many2many(
        'mobile_repair.device.color',
        string='Colores',
        help='Colores del dispositivo'
    )
    
    # Estado funcional
    powers_on = fields.Boolean(
        string='Enciende',
        default=True,
        help="¿El dispositivo enciende correctamente?"
    )
    
    # Estado físico
    physical_state = fields.Selection([
        ('screen_broken', 'Pantalla Rota'),
        ('scratches', 'Rayaduras'),
        ('dents', 'Golpes'),
        ('screen_lines', 'Líneas en Pantalla'),
        ('good', 'Buen Estado')
    ], string='Estado Físico', default='good', required=True)
    
    # Información de seguridad
    lock_type = fields.Selection([
        ('none', 'Sin bloqueo'),
        ('password', 'Contraseña'),
        ('pin', 'PIN'),
        ('pattern', 'Patrón')
    ], string='Tipo de bloqueo', default='none')
    
    has_lock_code = fields.Boolean(
        string='Tiene código de acceso',
        help="¿El cliente proporcionó el código de desbloqueo?"
    )
    
    # Accesorios incluidos
    accessory_ids = fields.Many2many(
        'mobile_repair.device.accessory', 
        string='Accesorios Incluidos',
        help="Accesorios que acompañan al dispositivo"
    )
    
    # Notas adicionales
    notes = fields.Text(
        string='Observaciones',
        help="Notas adicionales sobre el estado o características del dispositivo"
    )
    
    # Campo de visualización
    display_name = fields.Char(
        string='Nombre del Dispositivo',
        compute='_compute_display_name',
        store=True
    )
    
    # Estadísticas de reparaciones
    repair_count = fields.Integer(
        string='Reparaciones',
        compute='_compute_repair_stats',
        store=True
    )
    
    last_repair_date = fields.Datetime(
        string='Última Reparación',
        compute='_compute_repair_stats',
        store=True
    )
    
    @api.depends('brand_id.name', 'model_id.name', 'color_ids.name', 'device_code')
    def _compute_display_name(self):
        for device in self:
            parts = []
            
            if device.device_code:
                parts.append(f"[{device.device_code}]")
            
            if device.brand_id and device.model_id:
                parts.append(f"{device.brand_id.name} {device.model_id.name}")
            
            if device.color_ids:
                colors = ", ".join(device.color_ids.mapped('name'))
                parts.append(colors)
            
            device.display_name = " - ".join(parts) if parts else "Dispositivo"
    
    def _compute_repair_stats(self):
        """Calcula estadísticas de reparaciones"""
        for device in self:
            repair_domain = [('device_id', '=', device.id)]
            device.repair_count = self.env['mobile.repair.order'].search_count(repair_domain)
            
            last_repair = self.env['mobile.repair.order'].search(
                repair_domain, 
                order='date_received desc', 
                limit=1
            )
            device.last_repair_date = last_repair.date_received if last_repair else False
    
    @api.model_create_multi
    def create(self, vals_list):
        """Asigna código secuencial al crear dispositivo(s)"""
        for vals in vals_list:
            if not vals.get('device_code'):
                vals['device_code'] = self.env['ir.sequence'].next_by_code('mobile_repair.device') or 'DEV001'
        return super().create(vals_list)
    
    @api.constrains('imei')
    def _check_imei_unique(self):
        """Valida que el IMEI sea único si se proporciona"""
        for device in self:
            if device.imei:
                existing = self.search([
                    ('imei', '=', device.imei),
                    ('id', '!=', device.id)
                ])
                if existing:
                    raise ValidationError(f"Ya existe un dispositivo con IMEI {device.imei}")
    
    def action_view_repairs(self):
        """Acción para ver las reparaciones del dispositivo"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Reparaciones - {self.display_name}',
            'res_model': 'mobile.repair.order',
            'view_mode': 'list,kanban,form',
            'domain': [('device_id', '=', self.id)],
            'context': {
                'search_default_group_by_state': 1,
                'default_device_id': self.id
            }
        } 