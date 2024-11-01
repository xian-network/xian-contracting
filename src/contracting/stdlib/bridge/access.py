from contracting.execution.runtime import rt
from contextlib import ContextDecorator
from contracting.storage.driver import Driver
from typing import Any


class __export(ContextDecorator):
    def __init__(self, contract):
        self.contract = contract

    def __enter__(self, *args, **kwargs):
        driver = rt.env.get('__Driver') or Driver()

        if rt.context._context_changed(self.contract):
            current_state = rt.context._get_state()

            state = {
                'owner': driver.get_owner(self.contract),
                'caller': current_state['this'],
                'signer': current_state['signer'],
                'this': self.contract,
                'entry': current_state['entry'],
                'submission_name': current_state['submission_name']
            }

            rt.context._add_state(state)

            if state['owner'] is not None and state['owner'] != state['caller']:
                raise Exception('Caller is not the owner!')
        else:
            rt.context._ins_state()

    def __exit__(self, *args, **kwargs):
        rt.context._pop_state()


exports = {
    '__export': __export,
    'ctx': rt.context,
    'rt': rt,
    'Any': Any
}
