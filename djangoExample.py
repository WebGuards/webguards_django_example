# Python imports
import uuid
import os
import datetime
from dateutil.relativedelta import relativedelta

# Django imports
from django.db import models

# Project imports
from project.utils.models import ModelWithTimestamp


def get_file_format(filename):
    """
    Returns the format of given file.

    Parameters
    ----------
    filename: str
        The name of file.

    Returns
    -------
    str
        File format.
    """
    return filename.split('.')[-1]


def get_file_path(instance, filename):
    """
    Returns generated path for given file.

    Returns
    -------
    str
        New path for file.
    """
    ext = get_file_format(filename)
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('%s/%s' % (instance.__class__.__name__.lower(), filename))


class CSVFile(ModelWithTimestamp):
    DEFAULT_DATE_DELTA_DAYS = 7 # 7 days

    TYPE_INDEX = 1
    TYPE_SHEET = 2
    TYPE_BALKA = 3
    TYPE_SCHVELLER = 4
    TYPE_UGOLOK = 5
    TYPE_PROFIL_TRUBA = 6
    TYPE_KRUGLAYA_TRUBA = 7
    TYPE_FINAL_METHOD = 8
    TYPE_EXCHANGE_RATES = 9
    TYPE_SHARE_SPECIFICATIONS = 10

    FILE_TYPES = (
        (TYPE_INDEX, 'Composite index'),
        (TYPE_SHEET, 'Sheet g/p'),
        (TYPE_BALKA, 'Beam'),
        (TYPE_SCHVELLER, 'Channel'),
        (TYPE_UGOLOK, 'Corner'),
        (TYPE_PROFIL_TRUBA, 'Profile pipe'),
        (TYPE_KRUGLAYA_TRUBA, 'Round tube'),
        (TYPE_FINAL_METHOD, 'Indicator by final method'),
        (TYPE_EXCHANGE_RATES, 'Exchange rates'),
        (TYPE_SHARE_SPECIFICATIONS, 'Specification shares'),
    )

    TYPE_SIZES = {
        TYPE_INDEX: '',
        TYPE_SHEET: 'from 5 to 14 mm',
        TYPE_BALKA: '№20',
        TYPE_SCHVELLER: '№18',
        TYPE_UGOLOK: '63х5',
        TYPE_PROFIL_TRUBA: '100х4',
        TYPE_KRUGLAYA_TRUBA: '114х4',
        TYPE_FINAL_METHOD: '',
        TYPE_EXCHANGE_RATES: '',
        TYPE_SHARE_SPECIFICATIONS: ''
    }

    UAH = 1
    USD = 2
    EURO = 3

    CURRENCY_LIST = (
        (UAH, 'Hryvna'),
        (USD, 'Dollar'),
        (EURO, 'Euro'),
    )

    CURRENCY_FIELDS = {
        UAH: 'avg_uah',
        USD: 'avg_usd',
        EURO: 'avg_euro',
    }

    csv_file = models.FileField('File CSV', upload_to=get_file_path)
    file_type = models.PositiveSmallIntegerField('Download type', choices=FILE_TYPES)
    is_parsed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "CSV file"
        verbose_name_plural = "CSV files"

    def save(self, *args, **kwargs):
        edit_mode = self.pk
        super(CSVFile, self).save(*args, **kwargs)

        if not edit_mode:
            from project.core.utils import parse_csv
            parse_csv(self.id)

    @classmethod
    def get_class_mapping(cls):
        """
        Returns mapping of graphs and model classes for them.

        Returns
        -------
        dict
        """
        return {
            CSVFile.TYPE_SHEET: SheetGK,
            CSVFile.TYPE_BALKA: Balka,
            CSVFile.TYPE_SCHVELLER: Schveller,
            CSVFile.TYPE_UGOLOK: Ugolok,
            CSVFile.TYPE_PROFIL_TRUBA: ProfilTruba,
            CSVFile.TYPE_KRUGLAYA_TRUBA: KruglayaTruba,
        }

    @classmethod
    def get_dates(cls, date_from=None, date_to=None):
        """
        Returns dates for given period if exists.
        Otherwise, generate period by default.
        """

        # Translate string format to the date object.
        if date_from and isinstance(date_from, str):
            date_from = datetime.datetime.strptime(date_from, "%Y-%m-%d").date()
        if date_to and isinstance(date_to, str):
            date_to = datetime.datetime.strptime(date_to, "%Y-%m-%d").date()

        if not date_to:
            date_to = datetime.date.today()

        if not date_from:
            date_from = date_to - datetime.timedelta(days=cls.DEFAULT_DATE_DELTA_DAYS)

        dates = []
        while date_from <= date_to:
            dates.append(date_from)
            date_from += datetime.timedelta(days=1)

        return dates

    @classmethod
    def get_currencies(cls):
        """
        Returns data of currencies.

        Returns
        -------
        list
        """
        currencies = []
        for currency in cls.CURRENCY_LIST:
            currencies.append({
                    'code': currency[0],
                    'title': currency[1]
                })
        return currencies

    @classmethod
    def get_types_title_dict(cls):
        """
        Returns
        -------
        dict
        """
        types_dict = {}
        for type_ in cls.FILE_TYPES:
            types_dict[type_[0]] = '{} {}'.format(type_[1], cls.TYPE_SIZES[type_[0]])
        return types_dict

    @classmethod
    def get_graph_types(cls):
        """
        Returns data with grap types.

        Returns
        -------
        list
        """
        types = []
        exclude_types = (
            cls.TYPE_FINAL_METHOD,
            cls.TYPE_EXCHANGE_RATES,
            cls.TYPE_SHARE_SPECIFICATIONS
        )
        for t in cls.FILE_TYPES:
            if not t[0] in exclude_types:
                types.append({
                        'code': t[0],
                        'title': t[1]
                    })
        return types

    @classmethod
    def get_graph_names(cls):
        """
        Returns mapping of actual names for graph types.

        Returns
        -------
        dict
        """
        names = {}
        for t in cls.FILE_TYPES:
            names[t[0]] = t[1]
        return names

    @classmethod
    def get_fields_for_table(cls):
        """
        Returns mapping of fields for the table.

        Returns
        -------
        dict
        """
        return {
            cls.TYPE_SHEET: 'size_5_1500',
            cls.TYPE_BALKA: 'size_20',
            cls.TYPE_SCHVELLER: 'size_18',
            cls.TYPE_UGOLOK: 'size_63_5',
            cls.TYPE_PROFIL_TRUBA: 'size_100_50_4',
            cls.TYPE_KRUGLAYA_TRUBA: 'size_114_4'
        }

    @classmethod
    def get_specification_percent(cls):
        """
        Default values for specification.

        Returns
        -------
        dict
        """
        names_dict = CSVFile.get_graph_names()
        return {
            '{}'.format(cls.TYPE_SHEET): {
                'title': names_dict[cls.TYPE_SHEET],
                'value': 60,
            },
            '{}'.format(cls.TYPE_BALKA): {
                'title': names_dict[cls.TYPE_BALKA],
                'value': 10
            },
            '{}'.format(cls.TYPE_SCHVELLER): {
                'title': names_dict[cls.TYPE_SCHVELLER],
                'value': 10
            },
            '{}'.format(cls.TYPE_UGOLOK): {
                'title': names_dict[cls.TYPE_UGOLOK],
                'value': 10
            },
            '{}'.format(cls.TYPE_PROFIL_TRUBA): {
                'title': names_dict[cls.TYPE_PROFIL_TRUBA],
                'value': 5
            },
            '{}'.format(cls.TYPE_KRUGLAYA_TRUBA): {
                'title': names_dict[cls.TYPE_KRUGLAYA_TRUBA],
                'value': 5
            }
        }


####### Mixins ########


class CalculateMixin:
    CALCULATE_FIELDS = ()

    @classmethod
    def get_data_charts(cls, dates, currency=None):
        """
        Returns prepared data for charts by given dates.
        """

        # Invalid period
        if len(dates) < 2:
            return

        if currency:
            calculating_field = CSVFile.CURRENCY_FIELDS.get(int(currency))
        else:
            calculating_field = 'avg_uah'

        # Composite Index hasn't such fields, so let's fix it.
        if cls.__name__ == 'CompositeIndex':
            calculating_field = calculating_field.replace('avg_', '')

        calculated_data = []

        # Trying to find 'standard' value, which we want to use as the absolute value.
        standart_value = cls.objects.filter(date__lte=dates[0]).last()

        # TODO: Is this case possible?
        if not standart_value:
            return

        standart_value = getattr(standart_value, calculating_field)
        data_from_db = cls.objects.filter(date__gte=dates[0], date__lte=dates[-1])

        # Go across each date in dates list.
        for step_date in dates:
            step_value = data_from_db.filter(date=step_date).first()

            step_value = getattr(step_value, calculating_field) if step_value else standart_value
            if standart_value == 0:
                calculated_data.append(step_value)
            else:
                calculated_data.append((step_value*100)/standart_value)

        return calculated_data

    @classmethod
    def grahp_specification_data(cls, dates, currency=None, **kwargs):
        """
        Returns data for the graphic with the custom specification.
        """

        # Invalid period
        if len(dates) < 2:
            return

        if currency:
            calculating_field = CSVFile.CURRENCY_FIELDS.get(int(currency))
        else:
            calculating_field = 'avg_uah'

        data_classes = CSVFile.get_class_mapping()
        calculated_data = []
        cached_data = {}

        standart_value = 0

        # Cache filtered data.
        for graph_key in kwargs.keys():
            klass = data_classes.get(int(graph_key))
            period_data = klass.objects.filter(date__gte=dates[0], date__lte=dates[-1])
            if not period_data.exists():
                period_data = klass.objects.filter(date__lte=dates[-1])
            cached_data[graph_key] = period_data

            # Why no data?
            if not period_data:
                continue

            standard_value += getattr(period_data.first(), calculating_field)*kwargs[graph_key]['value']

        # Go across each date in dates list.
        for step_date in dates:
            # Summ of all graphics according specification percent.
            summ = 0
            for graph_key in cached_data:
                data_step = cached_data[graph_key].filter(date=step_date).first()
                if not data_step:
                    data_step = cached_data[graph_key].filter(date__lte=step_date).last()
                if not data_step:
                    data_step = cached_data[graph_key].filter(date__gte=step_date).first()
                # Why no data?
                if not data_step:
                    continue
                summ += getattr(data_step, calculating_field)*kwargs[graph_key]['value']

            calculated_data.append((summ*100)/standart_value)

        return calculated_data

    @classmethod
    def get_data_table(cls, price_field):
        """
        Returns data to show on the table.
        """
        today = datetime.date.today()

        # Data for current data
        today_data = cls.objects.filter(date__lte=today).last()

        # Data for month ago
        month_ago = today - relativedelta(months=1)
        month_ago_data = cls.objects.filter(date__lte=month_ago).last()

        # Data for start of the year
        start_year_data = cls.objects.filter(date__year__gte=today.year).first()
        if not start_year_data:
            start_year_data = cls.objects.filter(date__year__lte=today.year).last()

        # Data for year ago
        year_ago = today - relativedelta(years=1)
        year_ago_data = cls.objects.filter(date__lte=year_ago).last()

        # Convert common data to prices
        today_data = getattr(today_data, price_field)
        month_ago_data = getattr(month_ago_data, price_field)
        start_year_data = getattr(start_year_data, price_field)
        year_ago_data = getattr(year_ago_data, price_field)

        data = {
            'current': today_data,
            'month_ago': ((today_data-month_ago_data)/month_ago_data)*100,
            'start_year': ((today_data-start_year_data)/start_year_data)*100,
            'year_ago': ((today_data-year_ago_data)/year_ago_data)*100,
        }
        return data
