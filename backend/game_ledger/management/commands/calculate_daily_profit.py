from django.core.management.base import BaseCommand
from django.db.models import Sum, F
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import logging

from game_ledger.models import GameAnalytics, DailyProfitStats

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate daily profit percentages for each game type and store in DailyProfitStats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Calculate for specific date (YYYY-MM-DD). Defaults to today.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculation even if record already exists',
        )

    def handle(self, *args, **options):
        # Determine target date
        if options['date']:
            try:
                target_date = timezone.datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        else:
            target_date = timezone.now().date()

        self.stdout.write(f'Calculating profit stats for {target_date}')

        # Check if record already exists
        existing_record = DailyProfitStats.objects.filter(date=target_date).first()
        if existing_record and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'Record for {target_date} already exists. Use --force to recalculate.'
                )
            )
            return

        # Calculate profit percentages by game type
        profit_data = self.calculate_profit_percentages(target_date)

        if not profit_data:
            self.stdout.write(
                self.style.WARNING(f'No game data found for {target_date}')
            )
            # Still create/update record with empty data
            profit_data = {}

        # Create or update record
        record, created = DailyProfitStats.objects.update_or_create(
            date=target_date,
            defaults={'profit_data': profit_data}
        )

        # Clear cache to ensure fresh data on next API call
        cache_key = 'daily_profit_stats_latest'
        try:
            cache.delete(cache_key)
            self.stdout.write(f'Cache cleared for key: {cache_key}')
        except Exception as cache_error:
            self.stdout.write(
                self.style.WARNING(f'Failed to clear cache: {cache_error}')
            )

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} profit stats for {target_date}: {profit_data}'
            )
        )

    def calculate_profit_percentages(self, target_date):
        """
        Calculate profit percentages for each game type for the given date.
        Formula: ((total_stakes - total_payouts - commission) / total_stakes) * 100
        Commission: 10% of total_stakes
        """
        # Query GameAnalytics for the target date, grouped by game_type
        game_stats = (
            GameAnalytics.objects
            .filter(created_at__date=target_date)
            .values('game_type')
            .annotate(
                total_stakes=Sum('stake_amount'),
                total_payouts=Sum('winning_amount')
            )
            .filter(total_stakes__gt=0)  # Avoid division by zero
        )

        profit_data = {}

        for stats in game_stats:
            game_type = stats['game_type']
            total_stakes = stats['total_stakes']
            total_payouts = stats['total_payouts']

            # Calculate commission (10% of total stakes)
            commission = total_stakes * Decimal('0.10')

            # Calculate house profit (stakes - payouts - commission)
            house_profit = total_stakes - total_payouts - commission

            # Calculate profit percentage
            profit_percentage = (house_profit / total_stakes) * 100

            # Round to 2 decimal places and convert to float for JSON storage
            profit_data[game_type] = round(float(profit_percentage), 2)

            logger.info(
                f'Game type: {game_type}, Stakes: {total_stakes}, '
                f'Payouts: {total_payouts}, Commission: {commission}, '
                f'Profit %: {profit_data[game_type]}'
            )

        return profit_data
