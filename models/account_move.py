from odoo import models, fields, api
from datetime import timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    calendar_event_id = fields.Many2one(
        'calendar.event',
        string='Evento de Calendario',
        copy=False,
        help='Evento de calendario asociado al vencimiento de esta factura'
    )
    
    def _should_sync_to_calendar(self):
        """Verifica si este comprobante debe sincronizarse al calendario"""
        self.ensure_one()
        
        # Obtener parámetros de configuración
        ICPSudo = self.env['ir.config_parameter'].sudo()
        sync_enabled = ICPSudo.get_param('account_due_date_calendar.sync_due_dates_to_calendar', False)
        sync_invoices = ICPSudo.get_param('account_due_date_calendar.sync_invoice_due_dates', False)
        
        if not sync_enabled or not sync_invoices:
            return False
        
        # Solo facturas de cliente y proveedor con fecha de vencimiento
        if self.move_type not in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'):
            return False
        
        if self.state != 'posted':
            return False
            
        if not self.invoice_date_due:
            return False
        
        # No sincronizar si ya está totalmente pagado
        if self.payment_state == 'paid':
            return False
        
        return True
    
    def _get_calendar_event_vals(self):
        """Prepara los valores para crear/actualizar el evento de calendario"""
        self.ensure_one()
        
        # Obtener configuración
        ICPSudo = self.env['ir.config_parameter'].sudo()
        user_ids_str = ICPSudo.get_param('account_due_date_calendar.calendar_due_date_user_ids', '[]')
        user_ids = eval(user_ids_str) if user_ids_str != '[]' else []
        alarm_days_str = ICPSudo.get_param('account_due_date_calendar.calendar_due_date_alarm_days', '3')
        try:
            alarm_days = int(alarm_days_str)
        except:
            alarm_days = 3
        
        # Tipo de comprobante
        move_type_labels = {
            'out_invoice': 'Factura de Cliente',
            'in_invoice': 'Factura de Proveedor',
            'out_refund': 'Nota de Crédito Cliente',
            'in_refund': 'Nota de Crédito Proveedor',
        }
        
        name = f"{move_type_labels.get(self.move_type, 'Comprobante')}: {self.name}"
        
        description = f"""
        <b>Comprobante:</b> {self.name}<br/>
        <b>Tipo:</b> {move_type_labels.get(self.move_type, self.move_type)}<br/>
        <b>Socio:</b> {self.partner_id.name}<br/>
        <b>Monto Total:</b> {self.amount_total} {self.currency_id.name}<br/>
        <b>Monto Adeudado:</b> {self.amount_residual} {self.currency_id.name}<br/>
        <b>Fecha de Vencimiento:</b> {self.invoice_date_due}
        """
        
        vals = {
            'name': name,
            'description': description,
            'start': self.invoice_date_due,
            'stop': self.invoice_date_due,
            'allday': True,
            'res_model': 'account.move',
            'res_id': self.id,
        }
        
        # Agregar tipo de evento si existe
        try:
            event_type = self.env.ref('account_due_date_calendar.calendar_event_type_due_date', raise_if_not_found=False)
            if event_type:
                vals['categ_ids'] = [(4, event_type.id)]
        except:
            # Si no existe, buscar o crear uno
            event_type = self.env['calendar.event.type'].search([('name', '=', 'Vencimiento Contable')], limit=1)
            if not event_type:
                event_type = self.env['calendar.event.type'].create({'name': 'Vencimiento Contable'})
            vals['categ_ids'] = [(4, event_type.id)]
        
        # Agregar usuarios si están configurados
        if user_ids:
            vals['partner_ids'] = [(6, 0, self.env['res.users'].browse(user_ids).mapped('partner_id').ids)]
        
        # Agregar alarma
        if alarm_days > 0:
            alarm_date = fields.Datetime.to_datetime(self.invoice_date_due) - timedelta(days=alarm_days)
            vals['alarm_ids'] = [(0, 0, {
                'alarm_type': 'notification',
                'duration': alarm_days,
                'interval': 'days',
                'name': f'{alarm_days} días antes',
            })]
        
        return vals
    
    def _sync_calendar_event(self):
        """Sincroniza el evento de calendario para este comprobante"""
        for move in self:
            if move._should_sync_to_calendar():
                vals = move._get_calendar_event_vals()
                
                if move.calendar_event_id:
                    # Actualizar evento existente
                    move.calendar_event_id.write(vals)
                else:
                    # Crear nuevo evento
                    event = self.env['calendar.event'].create(vals)
                    move.calendar_event_id = event
            elif move.calendar_event_id:
                # Si ya no debe sincronizarse, eliminar el evento
                move.calendar_event_id.unlink()
    
    def write(self, vals):
        """Override para sincronizar al modificar"""
        res = super().write(vals)
        
        # Campos que afectan la sincronización
        sync_fields = ['invoice_date_due', 'state', 'payment_state', 'amount_residual', 'partner_id']
        if any(field in vals for field in sync_fields):
            self._sync_calendar_event()
        
        return res
    
    def action_post(self):
        """Override para sincronizar al confirmar factura"""
        res = super().action_post()
        self._sync_calendar_event()
        return res
    
    def button_draft(self):
        """Override para eliminar evento al pasar a borrador"""
        res = super().button_draft()
        self.filtered('calendar_event_id').mapped('calendar_event_id').unlink()
        return res
    
    def unlink(self):
        """Override para eliminar eventos asociados"""
        self.filtered('calendar_event_id').mapped('calendar_event_id').unlink()
        return super().unlink()