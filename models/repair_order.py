# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

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
    
    # ✅ NUEVOS CAMPOS PARA TIMESTAMPS
    start_date = fields.Datetime(
        string='Fecha de Inicio Real',
        readonly=True,
        help="Fecha y hora real cuando se inició la reparación"
    )
    completion_date = fields.Datetime(
        string='Fecha de Finalización',
        readonly=True,
        help="Fecha y hora cuando se completó la reparación"
    )
    
    # ✅ CAMPO COMPUTADO PARA DURACIÓN
    duration_hours = fields.Float(
        string='Duración (Horas)',
        compute='_compute_duration_hours',
        store=True,
        help="Duración total de la reparación en horas"
    )
    
    # ✅ CAMPO DE PROGRESO VISUAL
    progress = fields.Float(
        string='Progreso (%)',
        compute='_compute_progress',
        help="Progreso visual de la reparación (0-100%)"
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
    
    # TIPO DE FALLA RELACIONADO
    failure_type_id = fields.Many2one(
        'mobile.fault',
        string='Tipo de Falla',
        help="Selecciona la falla principal reportada para esta orden"
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

    @api.depends('start_date', 'completion_date')
    def _compute_duration_hours(self):
        """
        Calcula la duración de la reparación en horas.
        """
        for record in self:
            if record.start_date and record.completion_date:
                delta = record.completion_date - record.start_date
                record.duration_hours = delta.total_seconds() / 3600
            else:
                record.duration_hours = 0.0

    @api.depends('status', 'repair_line_ids', 'technician_id')
    def _compute_progress(self):
        """
        Calcula el progreso visual basado en el estado y completitud.
        """
        for record in self:
            if record.status == 'draft':
                # Borrador: 0% base + 10% si tiene técnico + 15% si tiene líneas
                progress = 0
                if record.technician_id:
                    progress += 15
                if record.repair_line_ids:
                    progress += 10
                record.progress = progress
            elif record.status == 'in_progress':
                # En proceso: 25% base + puntos por completitud
                progress = 25
                if record.repair_line_ids:
                    progress += 25  # Tiene trabajos definidos
                if record.technician_id:
                    progress += 25  # Tiene técnico asignado
                record.progress = progress
            elif record.status == 'completed':
                record.progress = 100  # Completada = 100%
            elif record.status == 'canceled':
                record.progress = 0   # Cancelada = 0%
            else:
                record.progress = 0

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

    # ✅ NUEVAS VALIDACIONES INTELIGENTES
    
    @api.constrains('start_date', 'completion_date')
    def _check_completion_after_start(self):
        """
        Valida que la fecha de finalización sea posterior a la de inicio.
        """
        for record in self:
            if record.start_date and record.completion_date:
                if record.completion_date <= record.start_date:
                    raise ValidationError(
                        "La fecha de finalización debe ser posterior a la fecha de inicio."
                    )

    @api.constrains('repair_date')
    def _check_repair_date_not_future(self):
        """
        Advierte si la fecha de reparación está muy en el futuro.
        """
        for record in self:
            if record.repair_date:
                days_diff = (record.repair_date.date() - fields.Date.today()).days
                if days_diff > 30:
                    # No ValidationError, solo log para el administrador
                    record.message_post(
                        body=f"⚠️ <b>Advertencia:</b> La fecha de reparación está programada "
                             f"para {days_diff} días en el futuro ({record.repair_date.strftime('%d/%m/%Y')}). "
                             f"Verifique si es correcto.",
                        message_type='notification'
                    )
    
    @api.constrains('total_amount', 'estimated_cost')
    def _check_cost_variance(self):
        """
        Advierte si el costo real excede significativamente el estimado.
        """
        for record in self:
            if record.estimated_cost > 0 and record.total_amount > 0:
                variance = ((record.total_amount - record.estimated_cost) / record.estimated_cost) * 100
                if variance > 50:  # Más del 50% de diferencia
                    record.message_post(
                        body=f"💰 <b>Variación de costo detectada:</b><br/>"
                             f"• Costo estimado: {record.currency_id.symbol}{record.estimated_cost:,.2f}<br/>"
                             f"• Costo real: {record.currency_id.symbol}{record.total_amount:,.2f}<br/>"
                             f"• Variación: +{variance:.1f}%<br/>"
                             f"Considere revisar el presupuesto inicial.",
                        message_type='notification'
                    )

    @api.constrains('technician_id', 'status')
    def _check_technician_workload(self):
        """
        Advierte si el técnico tiene muchas reparaciones activas.
        """
        for record in self:
            if record.technician_id and record.status in ['draft', 'in_progress']:
                active_repairs = self.env['mobile.repair.order'].search_count([
                    ('technician_id', '=', record.technician_id.id),
                    ('status', 'in', ['draft', 'in_progress']),
                    ('id', '!=', record.id)
                ])
                
                if active_repairs >= 5:  # Más de 5 reparaciones activas
                    record.message_post(
                        body=f"👷 <b>Carga de trabajo alta:</b><br/>"
                             f"El técnico {record.technician_id.name} tiene {active_repairs + 1} "
                             f"reparaciones activas. Considere redistribuir la carga de trabajo.",
                        message_type='notification'
                    )

    # ✅ MÉTODOS DE ESTADO MEJORADOS

    def action_start_repair(self):
        """
        Cambia el estado de la orden a "en proceso".
        ✅ MEJORADO: Agrega logs, timestamps y validaciones adicionales.
        """
        for record in self:
            # Validación de estado previo
            if record.status != 'draft':
                raise UserError("Solo se pueden iniciar órdenes en estado borrador.")
            
            # ✅ VALIDACIÓN ADICIONAL: Verificar que hay un técnico asignado
            if not record.technician_id:
                raise UserError(
                    f"Debe asignar un técnico antes de iniciar la reparación de la orden {record.name}."
                )
            
            # ✅ TIMESTAMP AUTOMÁTICO
            record.start_date = fields.Datetime.now()
            
            # Cambiar estado
            record.status = 'in_progress'
            
            # ✅ LOG AUTOMÁTICO AL CHATTER
            record.message_post(
                body=f"🔧 <b>Reparación iniciada</b><br/>"
                     f"• Técnico asignado: {record.technician_id.name}<br/>"
                     f"• Fecha de inicio: {record.start_date.strftime('%d/%m/%Y %H:%M')}<br/>"
                     f"• Dispositivo: {record.device_id.display_name}",
                message_type='notification'
            )
            
            # ✅ NOTIFICAR AL TÉCNICO ASIGNADO
            if record.technician_id:
                record.message_post(
                    body=f"🔔 <b>Nueva reparación asignada</b><br/>"
                         f"Hola {record.technician_id.name}, se te ha asignado la reparación "
                         f"<b>{record.name}</b> del dispositivo {record.device_id.display_name}.",
                    partner_ids=[record.technician_id.partner_id.id],
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Reparación Iniciada',
                'message': f'La orden {self.name} ha sido iniciada correctamente.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_complete(self):
        """
        Cambia el estado de la orden a "completada".
        ✅ MEJORADO: Agrega logs, timestamps y validaciones adicionales.
        """
        for record in self:
            # Validación de estado previo
            if record.status not in ['draft', 'in_progress']:
                raise UserError("Solo se pueden completar órdenes en borrador o en proceso.")
            
            # ✅ VALIDACIÓN ADICIONAL: Verificar que hay líneas de reparación
            if not record.repair_line_ids:
                raise UserError(
                    f"No se puede completar la orden {record.name} sin líneas de reparación. "
                    "Agregue al menos un producto o servicio."
                )
            
            # ✅ TIMESTAMP AUTOMÁTICO
            record.completion_date = fields.Datetime.now()
            
            # Cambiar estado
            record.status = 'completed'
            
            # ✅ LOG AUTOMÁTICO AL CHATTER con duración
            duration_text = ""
            if record.start_date and record.completion_date:
                duration_text = f"<br/>• Duración: {record.duration_hours:.1f} horas"
            
            record.message_post(
                body=f"✅ <b>Reparación completada</b><br/>"
                     f"• Fecha de finalización: {record.completion_date.strftime('%d/%m/%Y %H:%M')}<br/>"
                     f"• Monto total: {record.currency_id.symbol}{record.total_amount:,.2f}<br/>"
                     f"• Técnico: {record.technician_id.name if record.technician_id else 'No asignado'}"
                     f"{duration_text}",
                message_type='notification'
            )
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '🎉 Reparación Completada',
                'message': f'La orden {self.name} ha sido completada exitosamente.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_cancel(self):
        """
        Cambia el estado de la orden a "cancelada".
        ✅ MEJORADO: Agrega logs y validaciones adicionales.
        """
        for record in self:
            # Validación de estado previo
            if record.status == 'completed':
                raise UserError("No se pueden cancelar órdenes completadas.")
            
            # ✅ VALIDACIÓN ADICIONAL: Confirmar si tiene factura
            if record.invoice_id and record.invoice_id.state == 'posted':
                raise UserError(
                    f"No se puede cancelar la orden {record.name} porque tiene una "
                    "factura confirmada. Cancele primero la factura."
                )
            
            # Guardar estado anterior para el log
            estado_anterior = dict(record._fields['status'].selection)[record.status]
            
            # Cambiar estado
            record.status = 'canceled'
            
            # ✅ LOG AUTOMÁTICO AL CHATTER
            record.message_post(
                body=f"❌ <b>Reparación cancelada</b><br/>"
                     f"• Estado anterior: {estado_anterior}<br/>"
                     f"• Fecha de cancelación: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>"
                     f"• Usuario: {self.env.user.name}",
                message_type='notification'
            )
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '⚠️ Orden Cancelada',
                'message': f'La orden {self.name} ha sido cancelada.',
                'type': 'warning',
                'sticky': False,
            }
        }

    def action_reset_to_draft(self):
        """
        Regresa el estado de la orden a "borrador".
        ✅ MEJORADO: Agrega logs y validaciones adicionales.
        """
        for record in self:
            # Validación existente
            if record.status == 'completed' and record.invoice_id:
                raise UserError("No se puede regresar a borrador una orden completada con factura.")
            
            # ✅ VALIDACIÓN ADICIONAL: Confirmar con el usuario
            if record.status == 'completed':
                # Limpiar fechas de completion al regresar a draft
                record.completion_date = False
            
            if record.status == 'in_progress':
                # Limpiar fecha de inicio si regresa desde en proceso
                record.start_date = False
            
            # Guardar estado anterior para el log
            estado_anterior = dict(record._fields['status'].selection)[record.status]
            
            # Cambiar estado
            record.status = 'draft'
            
            # ✅ LOG AUTOMÁTICO AL CHATTER
            record.message_post(
                body=f"🔄 <b>Orden regresada a borrador</b><br/>"
                     f"• Estado anterior: {estado_anterior}<br/>"
                     f"• Fecha de cambio: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>"
                     f"• Usuario: {self.env.user.name}",
                message_type='notification'
            )
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '🔄 Orden Reiniciada',
                'message': f'La orden {self.name} ha regresado a estado borrador.',
                'type': 'info',
                'sticky': False,
            }
        }

    # MÉTODOS EXISTENTES SIN CAMBIOS

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