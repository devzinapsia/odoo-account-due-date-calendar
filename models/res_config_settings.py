from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Campo principal
    sync_due_dates_to_calendar = fields.Boolean(
        string='Sincronizar fechas de Vencimiento con Calendario',
        config_parameter='account_due_date_calendar.sync_due_dates_to_calendar',
        help='Activa la sincronización automática de vencimientos al calendario'
    )
    
    # Campos dependientes
    sync_invoice_due_dates = fields.Boolean(
        string='Envía Vencimientos de Comprobantes',
        config_parameter='account_due_date_calendar.sync_invoice_due_dates',
        help='Sincroniza las fechas de vencimiento de facturas y otros comprobantes'
    )
    
    sync_move_line_due_dates = fields.Boolean(
        string='Envía Vencimientos de Asientos Contables',
        config_parameter='account_due_date_calendar.sync_move_line_due_dates',
        help='Sincroniza las fechas de vencimiento de las líneas de asientos contables'
    )
    
    # Usuarios que verán los eventos - SIN config_parameter porque es Many2many
    calendar_due_date_user_ids = fields.Many2many(
        'res.users',
        string='Usuarios que verán los vencimientos',
        help='Usuarios que recibirán los eventos de vencimiento en su calendario. '
             'Si está vacío, los eventos serán visibles para todos.'
    )
    
    # Anticipación de notificación - SIN config_parameter para manejar el 0
    calendar_due_date_alarm_days = fields.Integer(
        string='Días de anticipación para alarma',
        default=3,
        help='Número de días antes del vencimiento para crear una alarma'
    )
    
    @api.model
    def get_values(self):
        """Recuperar valores de configuración"""
        res = super(ResConfigSettings, self).get_values()
        
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        # Obtener los IDs de usuarios
        user_ids_str = ICPSudo.get_param('account_due_date_calendar.calendar_due_date_user_ids', '[]')
        try:
            user_ids = eval(user_ids_str) if user_ids_str else []
            res['calendar_due_date_user_ids'] = [(6, 0, user_ids)]
        except:
            res['calendar_due_date_user_ids'] = [(6, 0, [])]
        
        # Obtener días de anticipación (manejar explícitamente el 0)
        alarm_days = ICPSudo.get_param('account_due_date_calendar.calendar_due_date_alarm_days', '3')
        try:
            res['calendar_due_date_alarm_days'] = int(alarm_days)
        except:
            res['calendar_due_date_alarm_days'] = 3
        
        return res
    
    def set_values(self):
        """Guardar valores de configuración"""
        super(ResConfigSettings, self).set_values()
        
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        # Guardar los IDs de usuarios
        user_ids = self.calendar_due_date_user_ids.ids
        ICPSudo.set_param('account_due_date_calendar.calendar_due_date_user_ids', str(user_ids))
        
        # Guardar días de anticipación (incluso si es 0)
        ICPSudo.set_param('account_due_date_calendar.calendar_due_date_alarm_days', str(self.calendar_due_date_alarm_days))