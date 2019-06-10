# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['ConfigurationCompany', 'Configuration']


class ConfigurationCompany(ModelSQL):
    'Company Quality configuration'
    __name__ = 'quality.configuration.company'

    company = fields.Many2One('company.company', 'Company')
    sample_sequence = fields.Many2One('ir.sequence',
            'Sample Sequence', domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'quality.sample'),
                ], required=True)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class Configuration(metaclass=PoolMeta):
    __name__ = 'quality.configuration'

    sample_sequence = fields.Function(fields.Many2One('ir.sequence',
            'Sample Sequence', domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'quality.sample'),
                ], required=True),
        'get_company_config', setter='set_company_config')

    @classmethod
    def get_company_config(self, configs, names):
        pool = Pool()
        CompanyConfig = pool.get('quality.configuration.company')
        res = dict.fromkeys(names, {configs[0].id: None})
        company_configs = CompanyConfig.search([], limit=1)
        if len(company_configs) == 1:
            company_config, = company_configs
            for field_name in set(names):
                value = getattr(company_config, field_name, None)
                if value:
                    res[field_name] = {configs[0].id: value.id}
        return res

    @classmethod
    def set_company_config(self, configs, name, value):
        pool = Pool()
        CompanyConfig = pool.get('quality.configuration.company')
        company_configs = CompanyConfig.search([], limit=1)
        if len(company_configs) == 1:
            company_config, = company_configs
        else:
            company_config = CompanyConfig()
        setattr(company_config, name, value)
        company_config.save()
