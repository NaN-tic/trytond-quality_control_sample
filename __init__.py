#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from . import configuration
from . import quality


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationCompany,
        quality.Template,
        quality.Sample,
        module='quality_control_sample', type_='model')
    Pool.register(
        quality.SampleReport,
        module='quality_control_sample', type_='report')
