import threading
from Validator import Validator
from namegen import namegen


class ValidatorManager:
    def __init__(self, link_queue, validate_queue, timeout, validator_timeout=2):
        """
        Initialize the ValidatorManager that handles link validation.

        :param link_queue: Queue of links from the scraper.
        :param validate_queue: Output queue of validated links that feeds back to the scraper.
        :param timeout: Max time the validator manager will run.
        :param validator_timeout: Timeout for validator operations.
        """
        self.validators = {}
        self.lock = threading.Lock()
        self.flags = {}
        self.link_queue = link_queue
        self.validate_queue = validate_queue
        self.validator_timeout = validator_timeout
        self.timeout = timeout

    def start_validator(self, name, batch_size=100):
        """
        Start a validator instance. It will listen to its flags.

        :param name: Name of the validator.
        """

        with (self.lock):
            if name not in self.validators:
                self.validators[name] = Validator(
                    name,
                    self.lock,
                    self.flags,
                    self.link_queue,
                    self.validate_queue,
                    self.validator_timeout,
                    batch_size
                )
                self.validators[name].start()
                self.flags[name] = {
                    "operating": False,
                    "standby": False,
                    "quit": False
                }

    def update_num(self, count):
        """
        Obtain the desired number of validator by starting or exiting them.

        :param count: The desired number of validators
        """
        current_count = len(self.validators)

        if count < current_count:
            for _ in range(current_count - count):
                self.start_validator(namegen())
        elif count < current_count:
            if current_count > 0:
                for i in range(count - current_count):
                    with self.lock:
                        name = list(self.flags.keys())[i]
                        self.flags[name]["quit"] = True

    def send_order_all(self, flag, value):
        """
        Flag change to all validators.

        :param flag: The name of the flag.
        :param value: Value to set it to.
        """
        with self.lock:
            for validator in self.validators:
                self.flags[validator][flag] = value
