# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MobileBrand(models.Model):
    """
    Modelo para gestionar las marcas de dispositivos móviles.
    Ejemplo: Samsung, Apple, Huawei, etc.
    """
    _name = 'mobile.brand'
    _description = 'Marca de dispositivo móvil'
    _order = 'name'

    name = fields.Char(
        string='Marca', 
        required=True,
        help="Nombre de la marca del dispositivo móvil"
    )
    code = fields.Char(
        string='Código',
        required=True,
        help="Código único para identificar la marca"
    )
    descripcion = fields.Text(
        string='Descripción',
        help="Descripción adicional de la marca"
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help="Indica si la marca está activa"
    )
    model_ids = fields.One2many(
        'mobile.model', 
        'brand_id', 
        string='Modelos',
        help="Modelos disponibles para esta marca"
    )
    device_ids = fields.One2many(
        'mobile.device', 
        'brand_id', 
        string='Dispositivos',
        help="Dispositivos asociados a esta marca"
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código de la marca debe ser único!')
    ]

    def name_get(self):
        """Personaliza la visualización del nombre en los campos relacionados"""
        result = []
        for record in self:
            result.append((record.id, record.name))
        return result


class MobileModel(models.Model):
    """
    Modelo para gestionar los modelos específicos de cada marca.
    Ejemplo: iPhone 13, Galaxy S21, etc.
    """
    _name = 'mobile.model'
    _description = 'Modelo de dispositivo móvil'
    _order = 'brand_id, name'

    name = fields.Char(
        string='Modelo', 
        required=True,
        help="Nombre del modelo específico"
    )
    code = fields.Char(
        string='Código',
        required=True,
        help="Código único para identificar el modelo"
    )
    brand_id = fields.Many2one(
        'mobile.brand', 
        string='Marca', 
        required=True,
        ondelete='cascade',
        help="Marca a la que pertenece este modelo"
    )
    descripcion = fields.Text(
        string='Descripción',
        help="Descripción técnica del modelo"
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help="Indica si el modelo está activo"
    )
    device_ids = fields.One2many(
        'mobile.device', 
        'model_id', 
        string='Dispositivos',
        help="Dispositivos asociados a este modelo"
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código del modelo debe ser único!')
    ]

    def name_get(self):
        """Muestra marca y modelo juntos en los campos relacionados"""
        result = []
        for record in self:
            name = f"{record.brand_id.name} {record.name}" if record.brand_id else record.name
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Permite buscar por marca o modelo en los campos relacionados"""
        if args is None:
            args = []
        
        if name:
            # Buscar por nombre del modelo o nombre de la marca
            domain = ['|', ('name', operator, name), ('brand_id.name', operator, name)]
            records = self.search(domain + args, limit=limit)
            return records.name_get()
        
        return super(MobileModel, self).name_search(name, args, operator, limit)


class MobileDevice(models.Model):
    """
    Modelo principal para gestionar dispositivos móviles individuales.
    Representa cada dispositivo físico que ingresa para reparación.
    """
    _name = 'mobile.device'
    _description = 'Dispositivo Móvil'
    _order = 'display_name'

    # Información básica del dispositivo
    brand_id = fields.Many2one(
        'mobile.brand', 
        string='Marca', 
        required=True,
        help="Marca del dispositivo móvil"
    )
    model_id = fields.Many2one(
        'mobile.model',
        string='Modelo',
        required=True,
        domain="[('brand_id', '=', brand_id)]",
        help="Modelo específico del dispositivo"
    )
    
    # Identificadores únicos
    imei = fields.Char(
        string='IMEI',
        help="Número IMEI del dispositivo (identificador único)"
    )
    serial_number = fields.Char(
        string='Número de serie',
        help="Número de serie del dispositivo"
    )
    
    # Características físicas
    color = fields.Char(
        string='Color',
        help="Color del dispositivo"
    )
    
    # Estado funcional
    enciende = fields.Boolean(
        string='¿Enciende?',
        default=True,
        help="Indica si el dispositivo enciende correctamente"
    )
    garantia = fields.Boolean(
        string='En garantía',
        default=False,
        help="Indica si el dispositivo está en período de garantía"
    )
    
    # Campo computado para mostrar nombre completo
    display_name = fields.Char(
        string='Dispositivo', 
        compute='_compute_display_name', 
        store=True,
        help="Nombre completo del dispositivo (marca + modelo)"
    )
    
    # Relaciones
    fault_ids = fields.Many2many(
        'mobile.fault', 
        string='Fallas',
        help="Fallas reportadas en el dispositivo"
    )
    condicion_id = fields.Many2one(
        'mobile.device.condition', 
        string='Condición del equipo',
        help="Estado general del dispositivo"
    )

    # Información de seguridad
    tipo_bloqueo = fields.Selection([
        ('ninguno', 'Ninguno'),
        ('pin', 'PIN'),
        ('patron', 'Patrón'),
        ('contraseña', 'Contraseña'),
        ('huella', 'Huella dactilar'),
        ('facial', 'Reconocimiento facial'),
        ('otro', 'Otro'),
    ], 
        string='Tipo de bloqueo', 
        default='ninguno',
        help="Tipo de bloqueo de seguridad configurado en el dispositivo"
    )

    detalle_bloqueo = fields.Char(
        string='Detalle del bloqueo', 
        help='Información adicional sobre el bloqueo (ej: PIN conocido, patrón dibujado, etc.)'
    )

    # Accesorios
    accesorios = fields.Text(
        string='Accesorios entregados', 
        help='Lista de accesorios entregados junto con el dispositivo'
    )

    @api.depends('brand_id', 'model_id')
    def _compute_display_name(self):
        """
        Calcula el nombre de visualización del dispositivo combinando marca y modelo.
        """
        for record in self:
            marca = record.brand_id.name if record.brand_id else ''
            modelo = record.model_id.name if record.model_id else ''
            partes = [p for p in [marca, modelo] if p]
            record.display_name = ' - '.join(partes) if partes else 'Dispositivo sin especificar'

    @api.onchange('brand_id')
    def _onchange_brand_id(self):
        """
        Limpia el campo modelo cuando se cambia la marca para evitar inconsistencias.
        """
        if self.brand_id:
            # Limpiar el modelo actual si no pertenece a la nueva marca
            if self.model_id and self.model_id.brand_id != self.brand_id:
                self.model_id = False
        else:
            self.model_id = False

    def name_get(self):
        """Personaliza la visualización del nombre en los campos relacionados"""
        result = []
        for record in self:
            name = record.display_name or 'Dispositivo'
            if record.imei:
                name += f" (IMEI: {record.imei[-4:]})"  # Muestra últimos 4 dígitos del IMEI
            result.append((record.id, name))
        return result

    def action_repair(self):
        """
        Crea una nueva orden de reparación para este dispositivo.
        """
        self.ensure_one()
        return {
            'name': 'Nueva Orden de Reparación',
            'type': 'ir.actions.act_window',
            'res_model': 'mobile.repair.order',
            'view_mode': 'form',
            'context': {
                'default_device_id': self.id,
                'default_customer_id': False,  # Se debe seleccionar el cliente
            }
        }


class FaultCategory(models.Model):
    """
    Modelo para categorizar las fallas de los dispositivos.
    Permite una estructura jerárquica de categorías.
    """
    _name = 'mobile.fault.category'
    _description = 'Categoría de Fallas'
    _order = 'parent_id, name'
    _parent_name = 'parent_id'
    _parent_store = True

    name = fields.Char(
        string='Categoría', 
        required=True,
        help="Nombre de la categoría de falla"
    )
    code = fields.Char(
        string='Código',
        required=True,
        help="Código único para identificar la categoría"
    )
    parent_id = fields.Many2one(
        'mobile.fault.category', 
        string='Categoría padre',
        ondelete='cascade',
        help="Categoría padre en la jerarquía"
    )
    child_ids = fields.One2many(
        'mobile.fault.category', 
        'parent_id', 
        string='Subcategorías',
        help="Subcategorías dependientes"
    )
    descripcion = fields.Text(
        string='Descripción',
        help="Descripción de la categoría de falla"
    )
    parent_path = fields.Char(index=True)

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        """Evita la recursión infinita en la jerarquía de categorías"""
        if not self._check_recursion():
            raise models.ValidationError('No puedes crear categorías recursivas.')

    def name_get(self):
        """Muestra la jerarquía completa en el nombre"""
        result = []
        for record in self:
            names = []
            current = record
            while current:
                names.append(current.name)
                current = current.parent_id
            result.append((record.id, ' / '.join(reversed(names))))
        return result


class Fault(models.Model):
    """
    Modelo para gestionar las fallas específicas de los dispositivos.
    """
    _name = 'mobile.fault'
    _description = 'Falla de Dispositivo'
    _order = 'category_id, name'

    name = fields.Char(
        string='Falla', 
        required=True,
        help="Descripción específica de la falla"
    )
    code = fields.Char(
        string='Código',
        required=True,
        help="Código único para identificar la falla"
    )
    category_id = fields.Many2one(
        'mobile.fault.category', 
        string='Categoría de Falla',
        help="Categoría a la que pertenece esta falla"
    )
    descripcion = fields.Text(
        string='Descripción',
        help="Descripción detallada de la falla y posibles causas"
    )

    def name_get(self):
        """Incluye la categoría en la visualización del nombre"""
        result = []
        for record in self:
            name = record.name
            if record.category_id:
                name = f"[{record.category_id.name}] {name}"
            result.append((record.id, name))
        return result


class DeviceCondition(models.Model):
    """
    Modelo para definir el estado general de los dispositivos.
    Ejemplo: Excelente, Bueno, Regular, Malo, etc.
    """
    _name = 'mobile.device.condition'
    _description = 'Condición de Dispositivo'
    _order = 'name'

    name = fields.Char(
        string='Condición', 
        required=True,
        help="Estado general del dispositivo"
    )
    code = fields.Char(
        string='Código',
        required=True,
        help="Código único para identificar la condición"
    )
    descripcion = fields.Text(
        string='Descripción',
        help="Descripción detallada de lo que implica esta condición"
    )

    def name_get(self):
        """Personaliza la visualización del nombre"""
        result = []
        for record in self:
            result.append((record.id, record.name))
        return result


class MobileRepairConfig(models.TransientModel):
    """
    Modelo de configuración para el módulo de reparaciones móviles.
    Extiende las configuraciones generales de Odoo.
    """
    _name = 'mobile.repair.config.settings'
    _inherit = 'res.config.settings'
    _description = 'Configuración de Reparaciones Móviles'

    # Aquí puedes agregar campos de configuración específicos del módulo
    # Por ejemplo:
    # default_warranty_days = fields.Integer(
    #     string='Días de garantía por defecto',
    #     default=30,
    #     help="Días de garantía que se aplican por defecto a las reparaciones"
    # )
    
    pass  # Por ahora solo sirve como placeholder para futuras configuraciones