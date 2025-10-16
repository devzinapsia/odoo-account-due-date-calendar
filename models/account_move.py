def _get_calendar_event_vals(self):
    """Prepara los valores para crear/actualizar el evento de calendario"""
    self.ensure_one()
    
    # Obtener configuración
    ICPSudo = self.env['ir.config_parameter'].sudo()
    user_ids_str = ICPSudo.get_param('account_due_date_calendar.calendar_due_date_user_ids', '[]')
    user_ids = eval(user_ids_str) if user_ids_str != '[]' else []
    alarm_days = int(ICPSudo.get_param('account_due_date_calendar.calendar_due_date_alarm_days', 3))
    
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