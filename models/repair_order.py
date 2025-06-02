# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RepairOrder(models.Model):
    _name = 'mobile.repair.order'
    _description = 'Repair Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Habilita el chatter y funcionalidades de actividad
    _rec_name = 'name'
    _order = 'name desc, id desc'

    # Referencia única de la orden
    name = fields.Char(
        string='Referencia de Orden', 
        required=True, 
        copy=False, 
        readonly=True, 
        index=True, 
        default=lambda self: self._get_default_name()
    )
    
    # Información básica de la orden
    customer_id = fields.Many2one(
        'res.partner', 
        string='Cliente', 
        required=True, 
        index=True,
        help="Cliente propietario del dispositivo"
    )
    device_id = fields.Many2one(
        'mobile.device', 
        string='Dispositivo', 
        required=True,
        help="Dispositivo a reparar"
    )
    status = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completada'),
        ('canceled', 'Cancelada'),
    ], 
        string='Estado', 
        default='draft', 
        tracking=True,
        help="Estado actual de la orden de reparación"
    )
    
    technician_id = fields.Many2one(
        'res.users', 
        string='Técnico',
        help="Técnico asignado a la reparación"
    )
    repair_date = fields.Datetime(
        string='Fecha de reparación', 
        default=fields.Datetime.now,
        required=True,
        help="Fecha y hora de inicio de la reparación"
    )
    notes = fields.Text(
        string='Notas',
        help="Notas adicionales sobre la reparación"
    )

    # Información adicional de la reparación
    description = fields.Text(
        string='Descripción del problema',
        help="Descripción detallada del problema reportado por el cliente"
    )
    estimated_cost = fields.Monetary(
        string='Costo estimado',
        currency_field='currency_id',
        help="Costo estimado de la reparación"
    )
    actual_cost = fields.Monetary(
        string='Costo real', 
        compute='_compute_actual_cost',
        store=True,
        currency_field='currency_id',
        help="Costo real basado en las líneas de reparación"
    )
    delivery_date = fields.Date(
        string='Fecha estimada de entrega',
        help="Fecha estimada de entrega del dispositivo reparado"
    )
    priority = fields.Selection([
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], 
        string='Prioridad', 
        default='normal',
        help="Prioridad de la reparación"
    )

    # Líneas de reparación y total
    repair_line_ids = fields.One2many(
        'mobile.repair.line', 
        'order_id', 
        string='Líneas de Reparación',
        help="Productos y servicios utilizados en la reparación"
    )
    total_amount = fields.Monetary(
        string='Monto Total', 
        compute='_compute_total_amount', 
        store=True, 
        currency_field='currency_id',
        help="Monto total de la orden de reparación"
    )
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda', 
        default=lambda self: self.env.company.currency_id,
        required=True,
        help="Moneda utilizada en la orden"
    )

    # Integración con facturación
    invoice_id = fields.Many2one(
        'account.move', 
        string='Factura', 
        readonly=True, 
        copy=False,
        help="Factura generada para esta orden"
    )
    invoice_count = fields.Integer(
        string='Contador de Facturas', 
        compute='_compute_invoice_count',
        help="Número de facturas asociadas"
    )

    def _get_default_name(self):
        """Genera el nombre por defecto de la orden"""
        sequence = self.env['ir.sequence'].next_by_code('mobile.repair.order')
        if not sequence:
            # Fallback si no existe la secuencia
            year = fields.Datetime.now().year
            return f'REP/{year}/001'
        return sequence

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override del método create para asignar secuencia automáticamente.
        """
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                vals['name'] = self._get_default_name()
        return super(RepairOrder, self).create(vals_list)

    @api.depends('repair_line_ids.price_subtotal')
    def _compute_total_amount(self):
        """
        Calcula el monto total sumando los subtotales de cada línea de reparación.
        """
        for order in self:
            order.total_amount = sum(line.price_subtotal for line in order.repair_line_ids)

    @api.depends('total_amount')
    def _compute_actual_cost(self):
        """
        El costo real es igual al monto total calculado.
        """
        for order in self:
            order.actual_cost = order.total_amount

    @api.depends('invoice_id')
    def _compute_invoice_count(self):
        """
        Cuenta las facturas asociadas a la orden.
        """
        for order in self:
            order.invoice_count = 1 if order.invoice_id else 0

    @api.constrains('delivery_date', 'repair_date')
    def _check_dates(self):
        """
        Valida que la fecha de entrega no sea anterior a la fecha de reparación.
        """
        for record in self:
            if record.delivery_date and record.repair_date:
                repair_date_only = record.repair_date.date()
                if record.delivery_date < repair_date_only:
                    raise ValidationError(
                        "La fecha de entrega no puede ser anterior a la fecha de reparación."
                    )

    @api.constrains('estimated_cost')
    def _check_estimated_cost(self):
        """
        Valida que el costo estimado no sea negativo.
        """
        for record in self:
            if record.estimated_cost < 0:
                raise ValidationError("El costo estimado no puede ser negativo.")

    def action_start_repair(self):
        """
        Cambia el estado de la orden a "en proceso".
        """
        for record in self:
            if record.status != 'draft':
                raise ValidationError("Solo se pueden iniciar órdenes en estado borrador.")
            record.status = 'in_progress'
        return True

    def action_complete(self):
        """
        Cambia el estado de la orden a "completada".
        """
        for record in self:
            if record.status not in ['draft', 'in_progress']:
                raise ValidationError("Solo se pueden completar órdenes en borrador o en proceso.")
            record.status = 'completed'
        return True

    def action_cancel(self):
        """
        Cambia el estado de la orden a "cancelada".
        """
        for record in self:
            if record.status == 'completed':
                raise ValidationError("No se pueden cancelar órdenes completadas.")
            record.status = 'canceled'
        return True

    def action_reset_to_draft(self):
        """
        Regresa el estado de la orden a "borrador".
        """
        for record in self:
            if record.status == 'completed' and record.invoice_id:
                raise ValidationError("No se puede regresar a borrador una orden completada con factura.")
            record.status = 'draft'
        return True

    def action_create_invoice(self):
        """
        Genera una factura basada en las líneas de reparación.
        """
        self.ensure_one()
        
        if self.invoice_id:
            raise ValidationError("Esta orden ya tiene una factura asociada.")
            
        if not self.repair_line_ids:
            raise ValidationError("No puedes crear una factura sin líneas de reparación.")

        if self.status != 'completed':
            raise ValidationError("Solo se pueden facturar órdenes completadas.")

        # Preparar los valores para la factura
        invoice_vals = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'ref': self.name,
            'invoice_date': fields.Date.today(),
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [],
        }

        # Crear las líneas de factura basadas en las líneas de reparación
        for line in self.repair_line_ids:
            invoice_line_vals = {
                'product_id': line.product_id.id,
                'name': line.description or line.product_id.display_name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }
            
            # Agregar impuestos si el producto los tiene
            if line.product_id.taxes_id:
                invoice_line_vals['tax_ids'] = [(6, 0, line.product_id.taxes_id.ids)]
                
            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Crear la factura y asociarla a la orden
        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id

        return {
            'name': 'Factura de Cliente',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }

    def action_view_invoice(self):
        """
        Abre la vista de la factura asociada a la orden.
        """
        self.ensure_one()
        
        if not self.invoice_id:
            raise ValidationError("Esta orden no tiene factura asociada.")
            
        return {
            'name': 'Factura de Cliente',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }

    def name_get(self):
        """
        Personaliza la visualización del nombre de las órdenes.
        """
        result = []
        for record in self:
            name = record.name
            if record.customer_id:
                name += f" - {record.customer_id.name}"
            result.append((record.id, name))
        return result