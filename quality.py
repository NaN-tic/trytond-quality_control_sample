# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms. """
import datetime
from functools import reduce

from dominate.tags import div, img, span

from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.modules.html_report.dominate_report import DominateReport
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.tools import file_open
from trytond.transaction import Transaction


STATES = {
    'readonly': Eval('state') == 'done',
}
DEPENDS = ['state']


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    needs_sample = fields.Boolean('Needs Samples')


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'


class Sample(Workflow, ModelSQL, ModelView):
    'Quality Sample'
    __name__ = 'quality.sample'
    _rec_name = 'code'

    code = fields.Char('Code', readonly=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('done', 'Done')],
        'State', required=True, readonly=True)
    product = fields.Many2One('product.product', 'Product', required=True,
        domain=[
            ('template.needs_sample', '=', True),
        ],
        context={
            'company': Eval('company', -1),
            },
        states=STATES, depends=['company'])
    lot = fields.Many2One('stock.lot', 'Lot', domain=[
            ('product', '=', Eval('product'))],
        states=STATES)
    collection_date = fields.DateTime('Collection Date', required=True,
        states=STATES)
    tests = fields.One2Many('quality.test', 'document', 'Tests', states=STATES)
    company = fields.Many2One('company.company', 'Company', required=True,
        states=STATES)
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
                    'icon': 'tryton-forward',
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

    # From python-barcode
    @staticmethod
    def calculate_checksum(code):
        sum_ = lambda x, y: int(x) + int(y)
        evensum = reduce(sum_, code[::2])
        oddsum = reduce(sum_, code[1::2])
        return (10 - ((evensum + oddsum * 3) % 10)) % 10

    def get_barcode(self, name):
        if self.lot:
            code = "%s%s%s" % (self.product.id, self.lot.number, len(self.tests))
        else:
            code = "%s%s" % (self.product.id, len(self.tests))
        code = code.zfill(12)[:12]
        return "%s%s" % (code, self.calculate_checksum(code))

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Config = pool.get('quality.configuration')

        sequence = Config(1).sample_sequence
        for value in vlist:
            if not value.get('code'):
                value['code'] = sequence and sequence.get()
        return super(Sample, cls).create(vlist)

    @classmethod
    def copy(cls, samples, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default['code'] = None
        return super(Sample, cls).copy(samples, default=default)


class SampleReport(DominateReport):
    'Sample Report'
    __name__ = 'quality.sample.report'
    _single = True
    side_margin = 0

    @classmethod
    def css(cls, action, data, records):
        with file_open('quality_control_sample/label.css') as css_file:
            return css_file.read()

    @classmethod
    def css_body(cls, action, data, records):
        return cls.css(action, data, records) or ''

    @classmethod
    def header(cls, action, data, records):
        return None

    @classmethod
    def footer(cls, action, data, records):
        return None

    @classmethod
    def _tests_text(cls, sample):
        values = []
        for test in sample.tests:
            value = (
                test.render.external_description
                if test.raw.external_description else
                test.render.internal_description
                if test.raw.internal_description else
                test.render.number
                if test.raw.number else '')
            if value:
                values.append(value)
        return ', '.join(values)

    @classmethod
    def body(cls, action, data, records):
        sample, = records
        container = div(cls='label')
        with container:
            with div(cls='label-row label-main'):
                span(sample.product.render.rec_name, cls='label-product')
                tests_text = cls._tests_text(sample)
                if tests_text:
                    span(tests_text, cls='label-tests')
            if sample.raw.lot:
                div(sample.lot.render.number, cls='label-row label-lot')
            if sample.render.barcode:
                img(
                    cls='label-barcode',
                    src=cls.barcode(
                        'ean13',
                        sample.render.barcode,
                        module_height=7.5,
                        quiet_zone=0.8,
                        font_size=9,
                    ),
                )
        return container
