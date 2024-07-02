from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime, Timedelta


class TestSimpleVotingContract(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu', environment={'now': Datetime(2019, 1, 1)})
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract)

        self.c.raw_driver.commit()

        submission = self.c.get_contract('submission')

        # submit erc20 clone
        with open('./contracts/simple_vote.s.py') as f:
            code = f.read()
            submission.submit_contract(name='simple_vote', code=code, environment={'now': Datetime(2019, 1, 1)})

        self.simple_vote = self.c.get_contract('simple_vote')

    def tearDown(self):
        #self.c.raw_driver.flush()
        pass

    def test_votable_is_100_after_submission(self):
        self.assertEqual(self.simple_vote.votable.get(), 100)

    def test_in_election_is_false_after_submission(self):
        self.assertEqual(self.simple_vote.in_election.get(), False)

    def test_timedelta_set_to_one_week_after_submission(self):
        day = Timedelta(days=1)
        week = Timedelta(weeks=1)

        self.assertEqual(self.simple_vote.election_interval.get(), week)
        self.assertEqual(self.simple_vote.voting_period.get(), day)

    def test_cant_vote_right_after_submission(self):
        with self.assertRaises(Exception):
            self.simple_vote.vote(v=5)

    def test_last_election_end_time_is_same_as_submission_time_after_submission(self):
        self.assertEqual(self.simple_vote.last_election_end_time.get(), Datetime(2019, 1, 1))

    def test_can_vote_one_week_after_submission(self):
        self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)})

    def test_vote_after_one_week_updates_election_time(self):
        self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)})

        self.assertEqual(self.simple_vote.election_start_time.get(), Datetime(2019, 1, 10))

    def test_vote_after_one_week_records_vote(self):
        self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)})

        self.assertEqual(self.simple_vote.votes['stu'], 5)

    def test_cannot_vote_twice_in_one_round(self):
        self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)})
        with self.assertRaises(AssertionError):
            self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)})

    def test_multiple_senders_can_vote(self):
        self.simple_vote.vote(v=7, environment={'now': Datetime(2019, 1, 10)}, signer='a')
        self.simple_vote.vote(v=6, environment={'now': Datetime(2019, 1, 10)}, signer='b')
        self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)}, signer='c')
        self.simple_vote.vote(v=4, environment={'now': Datetime(2019, 1, 10)}, signer='d')
        self.simple_vote.vote(v=3, environment={'now': Datetime(2019, 1, 10)}, signer='e')
        self.simple_vote.vote(v=2, environment={'now': Datetime(2019, 1, 10)}, signer='f')
        self.simple_vote.vote(v=1, environment={'now': Datetime(2019, 1, 10)}, signer='g')

        self.assertEqual(self.simple_vote.votes['a'], 7)
        self.assertEqual(self.simple_vote.votes['b'], 6)
        self.assertEqual(self.simple_vote.votes['c'], 5)
        self.assertEqual(self.simple_vote.votes['d'], 4)
        self.assertEqual(self.simple_vote.votes['e'], 3)
        self.assertEqual(self.simple_vote.votes['f'], 2)
        self.assertEqual(self.simple_vote.votes['g'], 1)

    def test_election_ends_after_time_has_passed(self):
        self.simple_vote.vote(v=7, environment={'now': Datetime(2019, 1, 10)}, signer='a')
        self.simple_vote.vote(v=6, environment={'now': Datetime(2019, 1, 10)}, signer='b')
        self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)}, signer='c')
        self.simple_vote.vote(v=4, environment={'now': Datetime(2019, 1, 10)}, signer='d')
        self.simple_vote.vote(v=3, environment={'now': Datetime(2019, 1, 10)}, signer='e')
        self.simple_vote.vote(v=2, environment={'now': Datetime(2019, 1, 10)}, signer='f')

        self.assertEqual(self.simple_vote.in_election.get(), True)

        # last vote
        self.simple_vote.vote(v=1, environment={'now': Datetime(2020, 1, 1)}, signer='g')

        self.assertEqual(self.simple_vote.in_election.get(), False)

    def test_last_election_end_time_is_equal_to_the_last_vote(self):
        self.simple_vote.vote(v=7, environment={'now': Datetime(2019, 1, 10)}, signer='a')
        self.simple_vote.vote(v=6, environment={'now': Datetime(2019, 1, 10)}, signer='b')
        self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)}, signer='c')
        self.simple_vote.vote(v=4, environment={'now': Datetime(2019, 1, 10)}, signer='d')
        self.simple_vote.vote(v=3, environment={'now': Datetime(2019, 1, 10)}, signer='e')
        self.simple_vote.vote(v=2, environment={'now': Datetime(2019, 1, 10)}, signer='f')

        self.assertEqual(self.simple_vote.last_election_end_time.get(), Datetime(2019, 1, 1))

        self.simple_vote.vote(v=1, environment={'now': Datetime(2020, 1, 1)}, signer='g')

        self.assertEqual(self.simple_vote.last_election_end_time.get(), Datetime(2020, 1, 1))

        #print(self.simple_vote.votes['g'])

    def test_all_votes_deleted_after_vote_is_done(self):
        self.simple_vote.vote(v=7, environment={'now': Datetime(2019, 1, 10)}, signer='a')
        self.simple_vote.vote(v=6, environment={'now': Datetime(2019, 1, 10)}, signer='b')
        self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)}, signer='c')
        self.simple_vote.vote(v=4, environment={'now': Datetime(2019, 1, 10)}, signer='d')
        self.simple_vote.vote(v=3, environment={'now': Datetime(2019, 1, 10)}, signer='e')
        self.simple_vote.vote(v=2, environment={'now': Datetime(2019, 1, 10)}, signer='f')

        self.assertEqual(self.simple_vote.votes['a'], 7)
        self.assertEqual(self.simple_vote.votes['b'], 6)
        self.assertEqual(self.simple_vote.votes['c'], 5)
        self.assertEqual(self.simple_vote.votes['d'], 4)
        self.assertEqual(self.simple_vote.votes['e'], 3)
        self.assertEqual(self.simple_vote.votes['f'], 2)

        self.simple_vote.vote(v=1, environment={'now': Datetime(2020, 1, 1)}, signer='g')

        # because the client still requires at least one entry on the hash to be existance (feature to extract
        # variable names from compiled contract still doesn't exist) we have to check via the raw driver

        self.assertEqual(self.c.raw_driver.get('simple_vote.votes:a'), None)
        self.assertEqual(self.c.raw_driver.get('simple_vote.votes:b'), None)
        self.assertEqual(self.c.raw_driver.get('simple_vote.votes:c'), None)
        self.assertEqual(self.c.raw_driver.get('simple_vote.votes:d'), None)
        self.assertEqual(self.c.raw_driver.get('simple_vote.votes:e'), None)
        self.assertEqual(self.c.raw_driver.get('simple_vote.votes:f'), None)
        self.assertEqual(self.c.raw_driver.get('simple_vote.votes:g'), None)

    def test_post_election_sets_new_value_to_median(self):
        values = [360, 6920, 118, 149, 656, 635, 511, 1770, 362, 215,
                  575, 743, 485, 567, 842, 491, 973, 893, 196, 245]

        self.simple_vote.vote(v=values[0], environment={'now': Datetime(2019, 1, 10)}, signer='a')
        self.simple_vote.vote(v=values[1], environment={'now': Datetime(2019, 1, 10)}, signer='b')
        self.simple_vote.vote(v=values[2], environment={'now': Datetime(2019, 1, 10)}, signer='c')
        self.simple_vote.vote(v=values[3], environment={'now': Datetime(2019, 1, 10)}, signer='d')
        self.simple_vote.vote(v=values[4], environment={'now': Datetime(2019, 1, 10)}, signer='e')
        self.simple_vote.vote(v=values[5], environment={'now': Datetime(2019, 1, 10)}, signer='f')
        self.simple_vote.vote(v=values[6], environment={'now': Datetime(2019, 1, 10)}, signer='g')
        self.simple_vote.vote(v=values[7], environment={'now': Datetime(2019, 1, 10)}, signer='h')
        self.simple_vote.vote(v=values[8], environment={'now': Datetime(2019, 1, 10)}, signer='i')
        self.simple_vote.vote(v=values[9], environment={'now': Datetime(2019, 1, 10)}, signer='j')
        self.simple_vote.vote(v=values[10], environment={'now': Datetime(2019, 1, 10)}, signer='k')
        self.simple_vote.vote(v=values[11], environment={'now': Datetime(2019, 1, 10)}, signer='l')
        self.simple_vote.vote(v=values[12], environment={'now': Datetime(2019, 1, 10)}, signer='m')
        self.simple_vote.vote(v=values[13], environment={'now': Datetime(2019, 1, 10)}, signer='n')
        self.simple_vote.vote(v=values[14], environment={'now': Datetime(2019, 1, 10)}, signer='o')
        self.simple_vote.vote(v=values[15], environment={'now': Datetime(2019, 1, 10)}, signer='p')
        self.simple_vote.vote(v=values[16], environment={'now': Datetime(2019, 1, 10)}, signer='q')
        self.simple_vote.vote(v=values[17], environment={'now': Datetime(2019, 1, 10)}, signer='r')
        self.simple_vote.vote(v=values[18], environment={'now': Datetime(2019, 1, 10)}, signer='s')

        self.simple_vote.vote(v=values[19], environment={'now': Datetime(2020, 1, 10)}, signer='t')

        self.assertEqual(self.simple_vote.votable.get(), 539)
        self.assertEqual(self.simple_vote.get_votable(), 539)
