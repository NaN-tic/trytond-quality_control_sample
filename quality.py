# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms. """
import datetime
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.modules.jasper_reports.jasper import JasperReport
from functools import reduce

__all__ = ['Template', 'Sample', 'SampleReport']

STATES = {
    'readonly': Eval('state') == 'done',
}
DEPENDS = ['state']


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    needs_sample = fields.Boolean('Needs Samples')


class Sample(Workflow, ModelSQL, ModelView):
    'Quality Sample'
    __name__ = 'quality.sample'
    _rec_name = 'code'

    code = fields.Char('Code', select=True, readonly=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
        ], 'State', required=True, readonly=True)
    product = fields.Many2One('product.product', 'Product', required=True,
        domain=[
            ('template.needs_sample', '=', True),
        ], states=STATES, depends=DEPENDS)
    lot = fields.Many2One('stock.lot', 'Lot', required=True, domain=[
            ('product', '=', Eval('product')),
        ], states=STATES, depends=DEPENDS + ['product'])
    collection_date = fields.DateTime('Collection Date', required=True,
        states=STATES, depends=DEPENDS)
    tests = fields.One2Many('quality.test', 'document', 'Tests', states=STATES,
        depends=DEPENDS)
    company = fields.Many2One('company.company', 'Company', required=True,
        select=True, states=STATES, depends=DEPENDS)
    barcode = fields.Function(fields.Char('Barcode'), 'get_barcode')

    @classmethod
    def __setup__(cls):
        super(Sample, cls).__setup__()
        cls._transitions |= set((
                ('draft', 'done'),
                ))
        cls._buttons.update({
                'done': {
                    'invisible': Eval('state') != 'draft',
                    'icon': 'tryton-go-next',
                    },
                 })

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, samples):
        pass

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_collection_date():
        return datetime.datetime.now()

    #From python-barcode
    @staticmethod
    def calculate_checksum(code):
        sum_ = lambda x, y: int(x) + int(y)
        evensum = reduce(sum_, code[::2])
        oddsum = reduce(sum_, code[1::2])
        return (10 - ((evensum + oddsum * 3) % 10)) % 10

    def get_barcode(self, name):
        code = "%s%s%s" % (self.product.id, self.lot.number, len(self.tests))
        code = code.zfill(12)[:12]
        return "%s%s" % (code, self.calculate_checksum(code))

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Config = pool.get('quality.configuration')
        Sequence = pool.get('ir.sequence')

        sequence = Config(1).sample_sequence
        for value in vlist:
            if not value.get('code'):
                value['code'] = Sequence.get_id(sequence.id)
        return super(Sample, cls).create(vlist)

    @classmethod
    def copy(cls, samples, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default['code'] = None
        return super(Sample, cls).copy(samples, default=default)


class SampleReport(JasperReport):
    'Sample Report'
    __name__ = 'quality.sample.report'
