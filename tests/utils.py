# from contracting.storage._driver import Driver
# from unittest import TestCase
# from contracting.config import MASTER_DB, DB_PORT
# from contracting.interpreter.parser import Parser
#
#
# class TestCaseHeader(TestCase):
#
#     def setUp(self):
#         print('\n{}'.format('#' * 128))
#         print('\t', self.id)
#         print('{}\n'.format('#' * 128))
#
#
# # class TestExecutor(TestCaseHeader):
# #
# #     @classmethod
# #     def setUpClass(cls):
# #         cls.r = Driver(host='localhost', port=DB_PORT, storage=MASTER_DB)
# #         cls.r.flush()
# #         cls.reset()
# #
# #     @classmethod
# #     def reset(cls, metering=False, concurrency=False):
# #         cls.r.flush()
# #         cls.ex = Executor(metering=metering, concurrency=concurrency)
# #
# #     @classmethod
# #     def flush(cls):
# #         cls.r.flush()
# #     #
# #     # @classmethod
# #     # def tearDownClass(cls):
# #     #     Parser.initialized = False
#
#
# class MockExecutor:
#     def __init__(self, *args, **kwargs):
#         self._driver = Driver(host='localhost', port=DB_PORT, storage=MASTER_DB)
#         self._driver.flush()
#         Parser.executor = self
#         if not Parser.parser_scope.get('rt'):
#             Parser.parser_scope['rt'] = {}
#         Parser.parser_scope['rt'].update({
#             'contract': 'sample',
#             'sender': 'falcon',
#             'author': '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
#         })
#
#
# class TestDataTypes(TestCaseHeader):
#
#     def setUp(self):
#         self.contract_id = self.id().split('.')[-1]
#         self.ex = MockExecutor()
#         Parser.parser_scope['rt']['contract'] = self.contract_id
#         super().setUp()
