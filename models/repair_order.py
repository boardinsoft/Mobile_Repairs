from odoo import models, fields, api

class RepairOrder(models.Model):
    _name = 'mobile.repair.order'
    _description = 'Repair Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Referencia de Orden', 
        required=True, 
        copy=False, 
        readonly=True, 
        index=True, 
        default=lambda self: self.env['ir.sequence'].next_by_code('mobile.repair.order') or 'New'
    )
    customer_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    device_id = fields.Many2one('mobile.device', string='Dispositivo', required=True, tracking=True)
    status = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completada'),
        ('canceled', 'Cancelada'),
    ], string='Estado', default='draft', tracking=True)
    technician_id = fields.Many2one('res.users', string='Técnico')
    repair_date = fields.Datetime(string='Fecha de reparación', default=fields.Datetime.now)
    notes = fields.Text(string='Notas')
    
    # Campos adicionales recomendados
    description = fields.Text(string='Descripción del problema')
    estimated_cost = fields.Float(string='Costo estimado')
    actual_cost = fields.Float(string='Costo real')
    delivery_date = fields.Date(string='Fecha estimada de entrega')
    priority = fields.Selection([
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], string='Prioridad', default='normal')

    @api.model
    def create(self, vals_list):
        # Manejar tanto dict como list
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        # Generar secuencia si no existe
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('mobile.repair.order') or 'New'

        return super(RepairOrder, self).create(vals_list)

    def action_start_repair(self):
        """Iniciar reparación"""
        self.status = 'in_progress'
        return True

    def action_complete(self):
        """Completar reparación"""
        self.status = 'completed'
        return True

    def action_cancel(self):
        """Cancelar reparación"""
        self.status = 'canceled'
        return True

    def action_reset_to_draft(self):
        """Regresar a borrador"""
        self.status = 'draft'
        return True