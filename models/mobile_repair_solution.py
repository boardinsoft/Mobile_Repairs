from odoo import models, fields, api

class MobileRepairSolution(models.Model):
    _name = 'mobile.repair.solution'
    _description = 'Soluciones de Reparación'
    _order = 'name'

    name = fields.Char('Nombre', required=True)
    description = fields.Text('Descripción')
    fault_ids = fields.Many2many('mobile.fault', string='Fallas Relacionadas')
    estimated_time = fields.Float('Tiempo Estimado (horas)')
    estimated_cost = fields.Float('Costo Estimado')
    notes = fields.Text('Notas Adicionales')
    active = fields.Boolean('Activo', default=True) 