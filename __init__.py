#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from configuration import *
from quality import *


def register():
    Pool.register(
        Configuration,
        ConfigurationCompany,
        Template,
        Sample,
        module='quality_control_sample', type_='model')
    Pool.register(
        SampleReport,
        module='quality_control_sample', type_='report')
