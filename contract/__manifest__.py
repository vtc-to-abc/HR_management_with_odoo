{
    'name': 'Custom contract',
    'summary': """Add more to contract""",
    'description': """yeah""",
    'author': "still me",
    'website': "https://cons.us",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'hr', 'hr_contract', 'hr_holidays'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_cus_views.xml',
    ],
    'installable': True,
    'application': True,
}