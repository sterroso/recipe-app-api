"""
Tests custom Django management commands.
"""
from unittest.mock import patch

from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


@patch('core.management.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    """Test commands."""

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for database if database ready."""
        patched_check.return_value = True

        call_command('wait_for_db')

        patched_check.assert_called_once_with(database=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waiting for database when getting OperationalError."""
        postgresql_errors = 2
        django_db_errors = 3
        total_calls = postgresql_errors + django_db_errors + 1

        patched_check.side_effect = [Psycopg2Error] * postgresql_errors + \
            [OperationalError] * django_db_errors + \
            [True]

        call_command('wait_for_db')

        self.assertEqual(patched_check.call_count, total_calls)
        patched_check.assert_called_with(database=['default'])
