# -*- coding: utf-8 -*-

from datetime import datetime

from pyface.api import ImageResource
from traits.api import \
    HasTraits, Regex, Date, Time, Button, on_trait_change
from traitsui.api import \
    View, Item, UItem, UCustom, HGroup, VGroup, DateEditor, TimeEditor

DATE_TIME_REGEX = '{year}-{month}-{day} {hour}:{minute}:{second}'.format(**{
    'year': '2\d{3}',  # 2000~2999
    'month': '(0[1-9]|1[012])',  # 01~12
    'day': '(0[1-9]|[12][0-9]|3[01])',  # 01~31
    'hour': '([01][0-9]|2[0-3])',  # 00~23
    'minute': '[0-5][0-9]',  # 00~59
    'second': '[0-5][0-9]',  # 00~59
})

DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class DateTime(HasTraits):

    date = Date(datetime.now().date())
    time = Time(datetime.now().time())
    date_time_str = Regex(regex=DATE_TIME_REGEX)

    config_button = Button(image=ImageResource('../../icons/Calendar'))

    @on_trait_change('date, time')
    def update_date_time_str(self):
        date_time = datetime.combine(self.date, self.time)
        self.date_time_str = date_time.strftime(DATE_TIME_FORMAT)

    def _date_time_str_default(self):
        date_time = datetime.combine(self.date, self.time)
        return date_time.strftime(DATE_TIME_FORMAT)

    def _date_time_str_changed(self):
        date_time = datetime.strptime(self.date_time_str, DATE_TIME_FORMAT)
        self.date = date_time.date()
        self.time = date_time.time()

    def _config_button_changed(self):
        self.edit_traits(view=View(
            VGroup(
                UCustom(
                    name='date',
                    label=u'日期',
                    editor=DateEditor(allow_future=False, format_str='%Y-%m-%d'),
                ),
                Item('_'),
                UCustom(
                    name='time',
                    label=u'时间',
                    editor=TimeEditor(format_str='%H:%M:%S'),
                    height=25
                ),
                show_labels=False,
            ),
            title=u'时间编辑',
            buttons=['OK'],
        ))

    traits_view = View(
        VGroup(
            HGroup(
                UItem(
                    name='date_time_str',
                    label=u'日期时间',
                    width=235,
                    height=25
                ),
                UCustom(
                    name='config_button',
                    label=u'选择日期和时间',
                    height=25,
                    width=25
                )
            ),
        ),
    )

# EOF
