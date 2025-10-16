# Due Date Calendar Synchronization

Odoo 18 module that automatically synchronizes invoice and accounting entry due dates with Odoo's calendar.

## Features

- ✅ Automatic synchronization of invoice due dates
- ✅ Synchronization of accounting entry line due dates
- ✅ Notifications X days in advance
- ✅ User filtering for event visibility
- ✅ Event categorization in calendar

## Requirements

- Odoo 18.0
- account module
- calendar module
- account_followup module (recommended)

## Installation

1. Copy the module to your addons folder
2. Update the application list
3. Install "Due Date Calendar Synchronization"

## Configuration

Go to **Accounting → Configuration → Settings → Due Date Calendar**

### Configuration Options

- **Sync Due Dates to Calendar**: Enable/disable the synchronization
- **Send Invoice Due Dates**: Sync invoice and bill due dates
- **Send Accounting Entry Due Dates**: Sync accounting entry line due dates
- **Users**: Select which users will see the due date events (leave empty for all users)
- **Days in Advance for Alarm**: Number of days before due date to create a notification

## Usage

Once configured, the module will automatically:

1. Create calendar events when invoices are posted
2. Create calendar events for accounting entry lines with due dates
3. Update events when due dates change
4. Remove events when invoices are paid or entries are reconciled

## Technical Details

- Events are created with the "Accounting Due Date" category
- Events link to the original invoice or accounting entry
- Only creates events for:
  - Posted invoices (customer/vendor)
  - Accounting lines with receivable/payable accounts
  - Unpaid/unreconciled items

## Author

Zinapsia - https://www.zinapsia.com

## License

LGPL-3

## Support

For issues or questions, please open an issue on GitHub.
