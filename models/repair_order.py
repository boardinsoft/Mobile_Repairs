# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

# ============================================================
# MODELO DE LÍNEAS DE PRESUPUESTO (DEFINIDO PRIMERO)
# ============================================================
class RepairQuoteLine(models.Model):
    _name = 'mobile.repair.quote.line'
    _description = 'Línea de Presupuesto de Reparación'
    _order = 'sequence, id'
    
    repair_order_id = fields.Many2one(
        'mobile.repair.order', string='Orden de Reparación', required=True, ondelete='cascade'
    )
    sequence = fields.Integer(string='Secuencia', default=10)
    
    display_type = fields.Selection([
        ('line_section', 'Sección'), ('line_note', 'Nota')],
        default=False, help="Tipo de línea especial."
    )
    
    product_id = fields.Many2one(
        'product.product', string='Producto/Servicio', domain=[('sale_ok', '=', True)],
        change_default=True
    )
    name = fields.Text(string='Descripción', required=True)
    quantity = fields.Float(
        string='Cantidad', digits='Product Unit of Measure', default=1.0
    )
    product_uom = fields.Many2one(
        'uom.uom', string='Unidad de Medida',
        domain="[('category_id', '=', product_uom_category_id)]"
    )
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    
    # --- Campos Financieros ---
    price_unit = fields.Float(string='Precio Unitario', digits='Product Price')
    discount = fields.Float(string='Descuento (%)', digits='Discount', default=0.0)
    tax_id = fields.Many2many('account.tax', string='Impuestos', domain=['|', ('active', '=', False), ('active', '=', True)])
    
    price_subtotal = fields.Monetary(
        string='Subtotal', currency_field='currency_id',
        compute='_compute_amount', store=True
    )
    price_total = fields.Monetary(
        string='Total', currency_field='currency_id',
        compute='_compute_amount', store=True
    )
    currency_id = fields.Many2one(related='repair_order_id.currency_id', store=True)

    @api.depends('quantity', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """Calcula el subtotal y total de la línea, aplicando descuentos e impuestos."""
        for line in self:
            if line.display_type:
                line.price_subtotal = line.price_total = 0.0
                continue
            
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price,
                line.repair_order_id.currency_id,
                line.quantity,
                product=line.product_id,
                partner=line.repair_order_id.customer_id
            )
            line.update({
                'price_subtotal': taxes['total_excluded'],
                'price_total': taxes['total_included'],
            })

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Actualiza información al cambiar producto, incluyendo los impuestos."""
        if not self.product_id:
            return
        
        self.name = self.product_id.get_product_multiline_description_sale()
        self.price_unit = self.product_id.list_price
        self.product_uom = self.product_id.uom_id
        
        # Cargar impuestos por defecto del producto
        self.tax_id = self.product_id.taxes_id.filtered(lambda t: t.company_id == self.env.company)

# ============================================================
# MODELO PRINCIPAL DE ÓRDENES DE REPARACIÓN
# ============================================================
class RepairOrder(models.Model):
    _name = 'mobile.repair.order'
    _description = 'Orden de Reparación Móvil'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    # CAMPOS PRINCIPALES
    name = fields.Char(
        string='Número', required=True, copy=False, readonly=True,
        index=True, default='Nuevo'
    )
    customer_id = fields.Many2one(
        'res.partner', string='Cliente', required=True, tracking=True, index=True
    )
    device_id = fields.Many2one(
        'mobile_repair.device', string='Dispositivo', required=True, tracking=True,
        index=True, help="Seleccionar dispositivo registrado"
    )
    problem_id = fields.Many2one(
        'mobile.repair.problem', string='Problema Reportado', required=True,
        tracking=True, help="Seleccionar problema del catálogo"
    )
    problem_description = fields.Text(
        string='Detalles Adicionales', tracking=True,
        help="Información específica adicional sobre el problema"
    )
    state = fields.Selection([
        ('draft', 'Recibido'),
        ('in_progress', 'En Reparación'),
        ('ready', 'Listo'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True, index=True)
    
    priority = fields.Selection([
        ('normal', 'Normal'), ('high', 'Alta'), ('urgent', 'Urgente')
    ], string='Prioridad', default='normal', tracking=True)

    technician_id = fields.Many2one(
        'res.users', string='Técnico', domain=[('active', '=', True)],
        tracking=True, index=True
    )

    # PESTAÑA DE DIAGNÓSTICO
    diagnosis = fields.Text(string='Diagnóstico Técnico', tracking=True)
    solution_applied = fields.Text(string='Solución Aplicada', tracking=True)

    # FECHAS CLAVE
    date_received = fields.Datetime(
        string='Fecha Recepción', default=fields.Datetime.now, required=True, index=True
    )
    date_started = fields.Datetime(string='Inicio Reparación', readonly=True, tracking=True)
    date_completed = fields.Datetime(string='Reparación Completa', readonly=True, tracking=True)
    date_delivered = fields.Datetime(string='Fecha Entrega', readonly=True, tracking=True)

    # LÍNEAS DE PRESUPUESTO Y TOTALES
    quote_line_ids = fields.One2many(
        'mobile.repair.quote.line', 'repair_order_id',
        string='Líneas de Presupuesto', copy=True
    )
    
    device_info = fields.Char(string='Información del Dispositivo', compute='_compute_device_info', store=True)
    device_brand = fields.Char(string='Marca', related='device_id.brand_id.name', store=True)
    device_model = fields.Char(string='Modelo', related='device_id.model_id.name', store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', default=_get_default_currency_id, required=True
    )
    company_id = fields.Many2one(
        'res.company', string='Compañía', default=lambda self: self.env.company, required=True
    )
    amount_untaxed = fields.Monetary(string='Base Imponible', compute='_compute_amounts', store=True)
    amount_tax = fields.Monetary(string='Impuestos', compute='_compute_amounts', store=True)
    amount_total = fields.Monetary(string='Importe Total', compute='_compute_amounts', store=True)

    # INTEGRACIÓN CON VENTAS Y FACTURACIÓN
    sale_order_id = fields.Many2one(
        'sale.order', string='Orden de Venta', readonly=True, copy=False, tracking=True
    )
    invoice_id = fields.Many2one(
        'account.move', string='Factura', compute='_compute_invoice_id', store=True,
        readonly=True, copy=False
    )
    invoice_state = fields.Selection(
        related='invoice_id.state', string='Estado Factura', readonly=True
    )
    invoiced = fields.Boolean(
        string='Facturado', compute='_compute_invoiced', store=True
    )

    # MÉTODOS COMPUTADOS
    @api.depends('quote_line_ids.price_total')
    def _compute_amounts(self):
        for order in self:
            amount_untaxed = sum(order.quote_line_ids.mapped('price_subtotal'))
            amount_total = sum(order.quote_line_ids.mapped('price_total'))
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_total - amount_untaxed,
                'amount_total': amount_total,
            })
    
    @api.depends('sale_order_id.invoice_ids')
    def _compute_invoice_id(self):
        for order in self:
            order.invoice_id = order.sale_order_id.invoice_ids and order.sale_order_id.invoice_ids[0] or False

    @api.depends('invoice_id.state')
    def _compute_invoiced(self):
        for record in self:
            record.invoiced = bool(record.invoice_id and record.invoice_id.state == 'posted')
    
    # CORRECCIÓN DE INDENTACIÓN EN LA LÍNEA SIGUIENTE
    @api.depends('device_id.brand_id.name', 'device_id.model_id.name', 'device_id.imei')
    def _compute_device_info(self):
        for record in self:
            if record.device_id:
                info_parts = []
                if record.device_id.brand_id:
                    info_parts.append(record.device_id.brand_id.name)
                if record.device_id.model_id:
                    info_parts.append(record.device_id.model_id.name)
                if record.device_id.imei:
                    info_parts.append(f"IMEI: {record.device_id.imei}")
                record.device_info = " - ".join(info_parts) if info_parts else "Sin información"
            else:
                record.device_info = "Sin dispositivo"

    # MÉTODOS DE NEGOCIO (ACCIONES DE BOTONES)
    def action_start_repair(self):
        self.ensure_one()
        if not self.technician_id:
            raise UserError("Debe asignar un técnico antes de iniciar la reparación.")
        self.write({
            'state': 'in_progress',
            'date_started': fields.Datetime.now()
        })
        return True

    def action_mark_ready(self):
        self.ensure_one()
        self.write({
            'state': 'ready',
            'date_completed': fields.Datetime.now()
        })
        return True

    def action_deliver(self):
        self.ensure_one()
        self.write({
            'state': 'delivered',
            'date_delivered': fields.Datetime.now()
        })
        return True

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})
        return True
    
    def action_create_invoice(self):
        self.ensure_one()
        if not self.amount_total:
            raise UserError("No se puede crear una factura con importe total cero.")

        order_lines = []
        for line in self.quote_line_ids.filtered(lambda l: not l.display_type):
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'product_uom_qty': line.quantity,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'tax_id': [(6, 0, line.tax_id.ids)],
            }))
        
        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'origin': self.name,
            'order_line': order_lines,
            'repair_order_id': self.id,
        })
        self.sale_order_id = sale_order.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Venta',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Venta',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factura',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    # MÉTODOS ESTÁNDAR DE ODOO
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('mobile.repair.order') or 'Error'
        return super().create(vals_list)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} - {record.customer_id.name}"
            result.append((record.id, name))
        return result

# ============================================================
# EXTENSIÓN DE OTROS MODELOS
# ============================================================
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    repair_order_id = fields.Many2one(
        'mobile.repair.order', string='Orden de Reparación', readonly=True, copy=False
    )

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    repair_orders_count = fields.Integer(
        string='Órdenes de Reparación', 
        compute='_compute_repair_orders_count'
    )
    
    def _compute_repair_orders_count(self):
        for partner in self:
            partner.repair_orders_count = self.env['mobile.repair.order'].search_count([
                ('customer_id', '=', partner.id)
            ])