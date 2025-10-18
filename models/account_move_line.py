from odoo import models, fields, api
from datetime import timedelta

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    calendar_event_id = fields.Many2one(
        'calendar.event',
        string='Evento de Calendario',
        copy=False,
        help='Evento de calendario asociado al vencimiento de esta línea'
    )
    
    def _should_sync_to_calendar(self):
        """Verifica si esta línea debe sincronizarse al calendario"""
        self.ensure_one()
        
        # Obtener parámetros de configuración
        ICPSudo = self.env['ir.config_parameter'].sudo()
        sync_enabled = ICPSudo.get_param('account_due_date_calendar.sync_due_dates_to_calendar', False)
        sync_move_lines = ICPSudo.get_param('account_due_date_calendar.sync_move_line_due_dates', False)
        
        if not sync_enabled or not sync_move_lines:
            return False
        
        # Solo líneas con fecha de vencimiento y cuenta por cobrar/pagar
        if not self.date_maturity:
            return False
        
        if self.move_id.state != 'posted':
            return False
        
        # Solo cuentas por cobrar/pagar
        if self.account_id.account_type not in ('asset_receivable', 'liability_payable'):
            return False
        
        # No sincronizar si está conciliada (pagada)
        if self.reconciled:
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
        
        account_type_label = 'Cuenta por Cobrar' if self.account_id.account_type == 'asset_receivable' else 'Cuenta por Pagar'
        
        name = f"{account_type_label}: {self.move_id.name} - {self.partner_id.name}"
        
        description = f"""
        <b>Asiento:</b> {self.move_id.name}<br/>
        <b>Cuenta:</b> {self.account_id.code} - {self.account_id.name}<br/>
        <b>Socio:</b> {self.partner_id.name}<br/>
        <b>Monto:</b> {abs(self.balance)} {self.company_currency_id.name}<br/>
        <b>Monto Pendiente:</b> {abs(self.amount_residual)} {self.company_currency_id.name}<br/>
        <b>Fecha de Vencimiento:</b> {self.date_maturity}
        """
        
        vals = {
            'name': name,
            'description': description,
            'start': self.date_maturity,
            'stop': self.date_maturity,
            'allday': True,
            'res_model': 'account.move.line',
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
            alarm_date = fields.Datetime.to_datetime(self.date_maturity) - timedelta(days=alarm_days)
            vals['alarm_ids'] = [(0, 0, {
                'alarm_type': 'notification',
                'duration': alarm_days,
                'interval': 'days',
                'name': f'{alarm_days} días antes',
            })]
        
        return vals
    
    def _sync_calendar_event(self):
        """Sincroniza el evento de calendario para esta línea"""
        for line in self:
            if line._should_sync_to_calendar():
                vals = line._get_calendar_event_vals()
                
                if line.calendar_event_id:
                    # Actualizar evento existente
                    line.calendar_event_id.write(vals)
                else:
                    # Crear nuevo evento
                    event = self.env['calendar.event'].create(vals)
                    line.calendar_event_id = event
            elif line.calendar_event_id:
                # Si ya no debe sincronizarse, eliminar el evento
                line.calendar_event_id.unlink()
    
    def write(self, vals):
        """Override para sincronizar al modificar"""
        res = super().write(vals)
        
        # Campos que afectan la sincronización
        sync_fields = ['date_maturity', 'reconciled', 'amount_residual', 'partner_id']
        if any(field in vals for field in sync_fields):
            self._sync_calendar_event()
        
        return res
    
    def unlink(self):
        """Override para eliminar eventos asociados"""
        self.filtered('calendar_event_id').mapped('calendar_event_id').unlink()
        return super().unlink()