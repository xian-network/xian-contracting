from contracting.execution import runtime
from contracting.storage.driver import Driver
from contracting.execution.module import install_database_loader, uninstall_builtins, enable_restricted_imports, disable_restricted_imports
from contracting.stdlib.bridge.decimal import ContractingDecimal, CONTEXT
from contracting.stdlib.bridge.random import Seeded
from contracting import constants
from copy import deepcopy

import importlib
import decimal


class Executor:
    def __init__(self,
                 production=False,
                 driver=None,
                 metering=True,
                 currency_contract='currency',
                 balances_hash='balances',
                 bypass_privates=False,
                 bypass_balance_amount=False,
                 bypass_cache=False):

        self.metering = metering
        self.driver = driver

        if not self.driver:
            self.driver = Driver(bypass_cache=bypass_cache)
        self.production = production

        self.currency_contract = currency_contract
        self.balances_hash = balances_hash

        self.bypass_privates = bypass_privates
        self.bypass_balance_amount = bypass_balance_amount  # For Stamp Estimation

        runtime.rt.env.update({'__Driver': self.driver})

    def wipe_modules(self):
        uninstall_builtins()
        install_database_loader()

    def execute(self, sender, contract_name, function_name, kwargs,
                environment={},
                auto_commit=False,
                driver=None,
                stamps=constants.DEFAULT_STAMPS,
                stamp_cost=constants.STAMPS_PER_TAU,
                metering=None) -> dict:

        current_driver_pending_writes = deepcopy(self.driver.pending_writes)
        self.driver.clear_transaction_writes()
        self.driver.clear_events()

        if not self.bypass_privates:
            assert not function_name.startswith(constants.PRIVATE_METHOD_PREFIX), 'Private method not callable.'

        if metering is None:
            metering = self.metering

        runtime.rt.env.update({'__Driver': self.driver})

        if driver:
            runtime.rt.env.update({'__Driver': driver})
        else:
            driver = runtime.rt.env.get('__Driver')

        install_database_loader(driver=driver)

        balances_key = None

        try:
            if metering:
                balances_key = (f'{self.currency_contract}'
                                f'{constants.INDEX_SEPARATOR}'
                                f'{self.balances_hash}'
                                f'{constants.DELIMITER}'
                                f'{sender}')

                if self.bypass_balance_amount:
                    balance = 9999999

                else:
                    balance = driver.get(balances_key)

                    if type(balance) == dict:
                        balance = ContractingDecimal(balance.get('__fixed__'))

                    if balance is None:
                        balance = 0

                assert balance * stamp_cost >= stamps, (f'Sender does not have enough stamps for the transaction. '
                                                        f'Balance at key {balances_key} is {balance}')

            runtime.rt.env.update(environment)
            status_code = 0

            # Multiply stamps by 1000 because we divide by it later
            # runtime.rt.set_up(stmps=stamps * 1000, meter=metering)

            runtime.rt.context._base_state = {
                'signer': sender,
                'caller': sender,
                'this': contract_name,
                'entry': (contract_name, function_name),
                'owner': driver.get_owner(contract_name),
                'submission_name': None
            }

            if runtime.rt.context.owner is not None and runtime.rt.context.owner != runtime.rt.context.caller:
                raise Exception(f'Caller {runtime.rt.context.caller} is not the owner {runtime.rt.context.owner}!')

            decimal.setcontext(CONTEXT)

            module = importlib.import_module(contract_name)
            func = getattr(module, function_name)

            # Add the contract name to the context on a submission call
            if contract_name == constants.SUBMISSION_CONTRACT_NAME:
                runtime.rt.context._base_state['submission_name'] = kwargs.get('name')

            for k, v in kwargs.items():
                if type(v) == float:
                    kwargs[k] = ContractingDecimal(str(v))

            enable_restricted_imports()
            runtime.rt.set_up(stmps=stamps * 1000, meter=metering)
            result = func(**kwargs)
            transaction_writes = deepcopy(driver.transaction_writes)
            events = deepcopy(driver.log_events)
            runtime.rt.tracer.stop()
            disable_restricted_imports()

            if auto_commit:
                driver.commit()

        except Exception as e:
            result = e
            status_code = 1

            # Revert the writes if the transaction fails
            driver.pending_writes = current_driver_pending_writes
            transaction_writes = {}
            events = {}
            if auto_commit:
                driver.flush_cache()

        finally:
            driver.clear_events()
            driver.clear_transaction_writes()
            runtime.rt.tracer.stop()

        #runtime.rt.tracer.stop()

        # Deduct the stamps if that is enabled
        stamps_used = runtime.rt.tracer.get_stamp_used()

        stamps_used = stamps_used // 1000
        stamps_used += 5

        if stamps_used > stamps:
            stamps_used = stamps

        if metering:
            assert balances_key is not None, 'Balance key was not set properly. Cannot deduct stamps.'

            to_deduct = stamps_used
            to_deduct /= stamp_cost
            to_deduct = ContractingDecimal(to_deduct)

            balance = driver.get(balances_key)
            if balance is None:
                balance = 0

            balance = max(balance - to_deduct, 0)

            driver.set(balances_key, balance)
            transaction_writes[balances_key] = balance

            if auto_commit:
                driver.commit()

        Seeded.s = False
        runtime.rt.clean_up()
        runtime.rt.env.update({'__Driver': driver})

        output = {
            'status_code': status_code,
            'result': result,
            'stamps_used': stamps_used,
            'writes': transaction_writes,
            'reads': driver.pending_reads,
            'events': events
        }

        disable_restricted_imports()
        return output
