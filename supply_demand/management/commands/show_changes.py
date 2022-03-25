import difflib
from datetime import timedelta

from django.core.management import BaseCommand, CommandParser
from django.utils.datetime_safe import date, datetime
from django.utils.translation import gettext as _

from supply_demand.models import Change


def change_date(value: str) -> date:
    return datetime.strptime(value, '%Y-%m-%d').date()


class Command(BaseCommand):
    help = _("Show an overview of changes")

    def add_arguments(self, parser: CommandParser):
        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        parser.add_argument('date', default=yesterday, nargs='?', type=change_date,
                            help=_('email changes of this day (default: {date})').format(date=yesterday))

    def handle(self, *args, **options):
        when = options['date']

        self.stdout.write(f"Donation/request changes of {when}:")
        self.stdout.write("")

        items = Change.objects.filter(when__year=when.year, when__month=when.month, when__day=when.day).order_by('when')
        if not items:
            self.stdout.write("- no changes")
            return

        differ = difflib.Differ()
        for item in items:
            self.stdout.write(f"- {item}")

            diff_lines = differ.compare(item.before.splitlines(),
                                        item.after.splitlines())
            diff = '\n  | '.join([line.rstrip() for line in diff_lines])
            self.stdout.write('  | ' + diff)
            self.stdout.write("")
