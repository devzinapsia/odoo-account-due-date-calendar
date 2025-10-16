{
    'name': 'Sincronización de Vencimientos con Calendario',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Sincroniza fechas de vencimiento de facturas y asientos con el calendario',
    'description': """
        Este módulo permite sincronizar automáticamente las fechas de vencimiento de:
        - Facturas y otros comprobantes (account.move)
        - Líneas de asientos contables (account.move.line)
        
        Las fechas se crean como eventos en el calendario de Odoo para mejor seguimiento.
    """,
    'author': 'Zinapsia',
    'website': 'https://www.zinapsia.com',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'calendar',
    ],
    'data': [
        'data/calendar_event_type_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}