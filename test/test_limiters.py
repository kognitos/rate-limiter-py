#!/usr/bin/env python
import utils
from unittest import TestCase
from mock import Mock, MagicMock, patch

from limiter import rate_limit, fungible_limiter

class BaseLimiterTest(TestCase):
    def setUp(self):
        self.limit = 10
        self.window = 100
        self.table_name = utils.random_string()
        self.resource_name = utils.random_string()

class FungibleTokenLimiterDecoratorTest(BaseLimiterTest):
    def setUp(self):
        super(FungibleTokenLimiterDecoratorTest, self).setUp()
        self.mock_manager = Mock()
        self.mock_manager.get_token = Mock()

    def test_call_account_id_pos(self):
        arg_1 = utils.random_string()
        arg_2 = utils.random_string()
        account_id = utils.random_string()
        account_id_pos = 2

        expected_manager_args = [(self.resource_name, account_id)]
        expected_limited_func_args = [(arg_1, arg_2, account_id)]

        func_to_limit = Mock()
        limiter = rate_limit(
            self.resource_name,
            self.table_name,
            self.limit,
            self.window,
            account_id_pos)
        limiter._manager = self.mock_manager

        rate_limited_func = limiter.__call__(func_to_limit)
        rate_limited_func(arg_1, arg_2, account_id)

        self.mock_manager.get_token.assert_called_with(account_id)
        func_to_limit.assert_called_with(arg_1, arg_2, account_id)

    def test_call_account_id_key(self):
        arg_1 = utils.random_string()
        arg_2 = utils.random_string()
        account_id = utils.random_string()
        account_id_key = 'account'

        expected_manager_args = [(self.resource_name, account_id)]
        expected_limited_func_args = [(arg_1, arg_2, {account_id_key: account_id})]

        func_to_limit = MagicMock()
        limiter = rate_limit(
            self.resource_name,
            self.table_name,
            self.limit,
            self.window,
            account_id_key=account_id_key)
        limiter._manager = self.mock_manager

        rate_limited_func = limiter.__call__(func_to_limit)
        rate_limited_func(arg_1, arg_2, account=account_id)

        self.mock_manager.get_token.assert_called_with(account_id)
        func_to_limit.assert_called_with(arg_1, arg_2, account=account_id)

    def test_manager_config_ctor_params(self):
        limiter = rate_limit(
            self.resource_name,
            self.table_name,
            self.limit,
            self.window)
        manager = limiter.manager

        self.assertEquals(self.table_name, manager.table_name)
        self.assertEquals(self.limit, manager.limit)
        self.assertEquals(self.window, manager.window)

    def test_manager_config_env_params(self):
        env_vars = {
            'FUNG_TABLE_NAME': str(self.table_name),
            'FUNG_LIMIT': str(self.limit),
            'FUNG_WINDOW': str(self.window)
        }

        with patch.dict('os.environ', env_vars):
            limiter = rate_limit(self.resource_name)
            manager = limiter.manager

            self.assertEquals(self.table_name, manager.table_name)
            self.assertEquals(self.limit, manager.limit)
            self.assertEquals(self.window, manager.window)

    @patch('limiter.limiters.FungibleTokenManager')
    def test_decoratored_account_id_pos(self, mock_manager_delegate):
        arg_1 = utils.random_string()
        arg_2 = utils.random_string()
        account_id = utils.random_string()

        mock_manager = Mock()
        mock_manager.return_value.get_token = Mock()
        mock_manager_delegate.return_value = mock_manager

        self.assertTrue(self._limited_func_account_id_pos(arg_1, arg_2, account_id))
        mock_manager.get_token.assert_called_with(account_id)

    @patch('limiter.limiters.FungibleTokenManager')
    def test_decoratored_account_id_key(self, mock_manager_delegate):
        arg_1 = utils.random_string()
        arg_2 = utils.random_string()
        account_id = utils.random_string()

        mock_manager = Mock()
        mock_manager.return_value.get_token = Mock()
        mock_manager_delegate.return_value = mock_manager

        self.assertTrue(self._limited_func_account_id_key(arg_1, arg_2, account_id=account_id))
        mock_manager.get_token.assert_called_with(account_id)

    @rate_limit('my-resource', 'my-table', 10, 100, account_id_pos=3)
    def _limited_func_account_id_pos(self, arg_1, arg_2, account_id):
        return True

    @rate_limit('my-resource', 'my-table', 10, 100)
    def _limited_func_account_id_key(self, arg_1, arg_2, account_id=None):
        return True

class FungibleTokenLimiterContextManagerTest(BaseLimiterTest):
    def setUp(self):
        super(FungibleTokenLimiterContextManagerTest, self).setUp()
        self.account_id = utils.random_string()

    @patch('limiter.limiters.FungibleTokenManager')
    def test_get_token_ctor_params(self, mock_manager_delegate):
        mock_manager = Mock()
        mock_manager.return_value.get_token = Mock()
        mock_manager_delegate.return_value = mock_manager

        with fungible_limiter(self.resource_name, self.account_id, self.table_name, self.limit, self.window):
            mock_manager.get_token.assert_called_with(self.account_id)

    @patch('limiter.limiters.FungibleTokenManager')
    def test_get_token_env_params(self, mock_manager_delegate):
        env_vars = {
            'FUNG_TABLE_NAME': str(self.table_name),
            'FUNG_LIMIT': str(self.limit),
            'FUNG_WINDOW': str(self.window)
        }

        with patch.dict('os.environ', env_vars):
            mock_manager = Mock()
            mock_manager.return_value.get_token = Mock()
            mock_manager_delegate.return_value = mock_manager

            with fungible_limiter(self.resource_name, self.account_id):
                mock_manager.get_token.assert_called_with(self.account_id)
