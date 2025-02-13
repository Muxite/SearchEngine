import threading
from Validator import Validator
from namegen import namegen


class ValidatorManager:
    def __init__(self, in_queue, out_queue, timeout, validator_timeout=2):
        """
        Initialize the ValidatorManager that handles link validation.

        :param in_queue: Queue of links from the scraper.
        :param out_queue: Output queue of validated links that feeds back to the scraper.
        :param timeout: Max time the validator manager will run.
        :param validator_timeout: Timeout for validator operations.
        """
        self.validators = {}
        self.validators_count = 0
        self.lock = threading.Lock()
        self.flags = {}
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.validator_timeout = validator_timeout
        self.timeout = timeout

    def start_validator(self, name, batch_size=1):
        """
        Start a validator instance. It will listen to its flags.

        :param batch_size:
        :param name: Name of the validator.
        """

        with (self.lock):
            if name not in self.validators:
                self.validators[name] = Validator(
                    name,
                    self.lock,
                    self.flags,
                    self.in_queue,
                    self.out_queue,
                    self.validator_timeout,
                    batch_size
                )
                self.validators[name].start()
                self.flags[name] = {
                    "operating": False,
                    "quit": False
                }

    def update_num(self, count):
        """
        Obtain the desired number of validator by starting or exiting them.

        :param count: The desired number of validators
        """

        if count > self.validators_count:
            for _ in range(self.validators_count - count):
                self.start_validator(namegen())
        elif count < self.validators_count:
            self.end_validators(self.validators_count - count)

    def send_order_all(self, flag, value):
        """
        Flag change to all validators.

        :param flag: The name of the flag.
        :param value: Value to set it to.
        """
        with self.lock:
            for validator in self.validators:
                self.flags[validator][flag] = value

    def end_validator(self, name):
        with self.lock:
            self.flags[name]["quit"] = True
        self.validators_count -= 1

    def end_validators(self, count):
        to_end = max(count, self.validators_count)
        ended = 0
        for validator in self.flags:
            if not self.flags[validator]["quit"]:
                self.end_validator(validator)
                ended += 1
                if ended == to_end:
                    break
