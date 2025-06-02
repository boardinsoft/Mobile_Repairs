# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RepairLine(models.Model):
    """
    Modelo para gestionar las líneas individuales de una orden de reparación.
    Cada línea representa un producto, servicio o repuesto utilizado en la reparación.
    """
    _name = 'mobile.repair.line'
    _description = 'Línea de Orden de Reparación'
    _order = 'order_id, sequence, id'

    # Relación con la orden principal
    order_id = fields.Many2one(
        'mobile.repair.order',
        string='Orden de Reparación',
        required=True,
        ondelete='cascade',
        index=True,
        help="Orden de reparación a la que pertenece esta línea"
    )

    # Campo de secuencia para ordenar las líneas
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help="Orden de visualización de las líneas"
    )

    # Campo de moneda relacionado con la orden (MOVIDO ANTES para evitar errores de referencia)
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        string='Moneda',
        readonly=True,
        store=True,
        help="Moneda utilizada en la orden de reparación"
    )

    # Producto o servicio
    product_id = fields.Many2one(
        'product.product',
        string='Producto/Servicio',
        required=True,
        domain="['|', ('purchase_ok', '=', True), ('sale_ok', '=', True)]",
        help="Producto, repuesto o servicio utilizado en la reparación"
    )

    # Descripción detallada
    description = fields.Text(
        string='Descripción',
        help="Descripción detallada del trabajo realizado o producto utilizado"
    )

    # Cantidad y precios
    quantity = fields.Float(
        string='Cantidad',
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
        help="Cantidad del producto o servicio"
    )

    price_unit = fields.Float(
        string='Precio Unitario',
        required=True,
        digits='Product Price',
        help="Precio unitario del producto o servicio"
    )

    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_price_subtotal',
        store=True,
        currency_field='currency_id',
        help="Subtotal de la línea (cantidad × precio unitario)"
    )

    # Campo para identificar si es un servicio
    is_service = fields.Boolean(
        string='Es Servicio',
        compute='_compute_is_service',
        store=True,
        help="Indica si el producto es un servicio"
    )

    # Unidad de medida
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de Medida',
        related='product_id.uom_id',
        readonly=True,
        help="Unidad de medida del producto"
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Actualiza automáticamente el precio unitario y la descripción
        cuando se selecciona un producto.
        """
        if not self.product_id:
            self.price_unit = 0.0
            self.description = ''
            return

        # Establecer el precio de venta del producto
        self.price_unit = self.product_id.lst_price

        # Si no hay descripción, usar el nombre del producto
        if not self.description:
            self.description = self.product_id.display_name or self.product_id.name

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        """
        Calcula el subtotal de cada línea de reparación.
        Subtotal = Cantidad × Precio Unitario
        """
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit

    @api.depends('product_id', 'product_id.type')
    def _compute_is_service(self):
        """
        Determina si el producto de la línea es un servicio.
        Los servicios no manejan stock físico.
        """
        for line in self:
            line.is_service = (line.product_id.type == 'service') if line.product_id else False

    @api.constrains('quantity')
    def _check_quantity(self):
        """
        Valida que la cantidad sea positiva.
        """
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(
                    f"La cantidad debe ser mayor a cero en la línea con producto '{line.product_id.display_name}'."
                )

    @api.constrains('price_unit')
    def _check_price_unit(self):
        """
        Valida que el precio unitario no sea negativo.
        Permitir precio cero si es necesario.
        """
        for line in self:
            if line.price_unit < 0:
                raise ValidationError(
                    f"El precio unitario no puede ser negativo en la línea con producto '{line.product_id.display_name}'."
                )

    def name_get(self):
        """
        Personaliza la visualización del nombre de las líneas de reparación.
        """
        result = []
        for line in self:
            name = f"{line.product_id.display_name or 'Sin Producto'}"
            if line.quantity != 1:
                name += f" (x{line.quantity})"
            result.append((line.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override del método create para establecer valores por defecto adicionales.
        """
        for vals in vals_list:
            # Si no se especifica descripción y hay un product_id, obtenerla del producto
            if vals.get('product_id') and not vals.get('description'):
                product = self.env['product.product'].browse(vals['product_id'])
                if product.exists():
                    vals['description'] = product.display_name or product.name

        return super(RepairLine, self).create(vals_list)

    def write(self, vals):
        """
        Override del método write para mantener consistencia en los datos.
        """
        # Si se cambia el producto y no hay nueva descripción, actualizar
        if (vals.get('product_id') and 'description' not in vals and 
            not self.env.context.get('skip_description_update_on_write')):
            product = self.env['product.product'].browse(vals['product_id'])
            if product.exists():
                vals['description'] = product.display_name or product.name

        return super(RepairLine, self).write(vals)