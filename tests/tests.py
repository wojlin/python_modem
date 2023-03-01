import json
import unittest
import subprocess
import logging
import os
import glob
import os
from copy import copy
import shutil
import numpy as np


from test_utils import create_random_text

class ModemTest(unittest.TestCase):
    MODULATION = ""
    BAUDRATE = 30

    BAUDRATES = []
    LENGTHS = []

    TEST_PATH = ""
    TEMP_PATH = ""
    COMM_CONFIG_PATH = ""
    TEST_CONFIG = {}
    @classmethod
    def setUpClass(cls):
        cls.TEST_PATH = os.path.dirname(os.path.realpath(__file__)) + "/"
        test_config_path = f"{cls.TEST_PATH}/tests_config.json"
        with open(test_config_path, 'r') as f:
            cls.TEST_CONFIG = json.loads(f.read())

        cls.MODULATION = cls.TEST_CONFIG["tested_modem"]


        cls.COMM_CONFIG_PATH = f"{'/'.join(cls.TEST_PATH.split('/')[:-2])}/configs/communication_config.json"
        cls.TEMP_PATH = cls.TEST_PATH + f"temp/{cls.MODULATION}-modulation/"




        min_baud = cls.TEST_CONFIG["advanced_test"]["baudrate_test_range"]["min"]
        max_baud = cls.TEST_CONFIG["advanced_test"]["baudrate_test_range"]["max"]
        amount = cls.TEST_CONFIG["advanced_test"]["baudrate_test_range"]["amount"]
        cls.BAUDRATES = np.linspace(min_baud, max_baud, num=amount, dtype=int).tolist()


        min_length = cls.TEST_CONFIG["advanced_test"]["length_test_range"]["min"]
        max_length = cls.TEST_CONFIG["advanced_test"]["length_test_range"]["max"]
        amount = cls.TEST_CONFIG["advanced_test"]["length_test_range"]["amount"]
        cls.LENGTHS = np.linspace(min_length, max_length, num=amount, dtype=int).tolist()




        path = cls.TEMP_PATH
        if path != "":
            shutil.rmtree(cls.TEMP_PATH, ignore_errors=True)
            os.makedirs(cls.TEMP_PATH)

    def setUp(self):
        self.comm_config = {}

        with open(self.COMM_CONFIG_PATH, 'r') as f:
            self.comm_config = json.loads(f.read())

        #print(self.comm_config)

    def tearDown(self):
        with open(self.COMM_CONFIG_PATH, 'w') as f:
            f.write(json.dumps(self.comm_config, sort_keys=False, indent=4))

    def length_check(self, length, modulation, baudrate):

        failures = []

        def failure_template(modulation, length, baudrate, message):
            return f"tc {modulation} {length} chars {baudrate} baudrate:\n{message}\n"

        text = create_random_text(length)

        test_path = os.path.dirname(os.path.realpath(__file__)) + "/"
        temp_path = self.TEMP_PATH
        program_path = f"{'/'.join(test_path.split('/')[:-2])}/main.py"
        comm_config_path = f"{'/'.join(test_path.split('/')[:-2])}/configs/communication_config.json"

        comm_config = {}
        with open(comm_config_path, 'r') as f:
            comm_config = json.loads(f.read())

        comm_config["baud_rate[bps]"] = baudrate
        #print(comm_config)
        with open(comm_config_path, 'w') as f:
            f.write(json.dumps(comm_config, sort_keys=False, indent=4))
        print()
        print("_"*50)
        print(f"length check of {length} chars and with {baudrate} baudrate")
        
        out_wav_name = f"{temp_path}{baudrate}-baudrate_{length}-chars_{modulation}-modulation.wav"
        out_txt_name = f"{temp_path}{baudrate}-baudrate_{length}-chars_{modulation}-modulation.txt"
        out_mod_analysis_name = f"{temp_path}{baudrate}-baudrate_{length}-chars_{modulation}-modulation_modulate.png"
        out_demod_analysis_name = f"{temp_path}{baudrate}-baudrate_{length}-chars_{modulation}-modulation_demodulate.png"
        
        print("launching modulation...")
        
        command = f'python3 {program_path} -a {out_mod_analysis_name} modulate -m {modulation} --i {text} -o {out_wav_name}'.split()

        p = subprocess.Popen(command, shell=False)
        p.wait()
        
        print("launching demodulation...")
        
        command = f'python3 {program_path} -a {out_demod_analysis_name} demodulate -m {modulation} --i {out_wav_name} -o {out_txt_name}'.split()
        p = subprocess.Popen(command, shell=False)
        p.wait()
        
        print("comparing modulated data with demodulated...")

        content = ''
        is_file_present = os.path.exists(out_txt_name)
        if not is_file_present:
            message = "program did not saved demodulated data to file"
            print(message)
            failures.append(failure_template(self.MODULATION, length, baudrate, message))

        with open(out_txt_name) as f:
            try:
                content = f.read()
                print(f'original text: "{text}"')
                print(f'received text: "{content}"')
            except UnicodeDecodeError:
                message = "decoding error when reading output file with standard utf-8 text"
                print(message)
                failures.append(failure_template(self.MODULATION, length, baudrate, message))

        if text != content:
            message = "input text does not match with output text"
            print(message)
            failures.append(failure_template(self.MODULATION, length, baudrate, message))
            print("|FAILED|")

        else:

            print("|PASSED|")

        print("_" * 50)

        return failures

    def test_basic(self):
        run = self.TEST_CONFIG["basic_test"]["run"]
        if run:
            baudrate = self.TEST_CONFIG["basic_test"]["baudrate"]
            length = self.TEST_CONFIG["basic_test"]["length"]

            failures = self.length_check(length, self.MODULATION, baudrate)
            self.assertEqual(0, len(failures))
        else:
            raise unittest.SkipTest("not enabled in test config")

    def test_advanced(self):
        run = self.TEST_CONFIG["advanced_test"]["run"]
        if run:
            failures = []
            for baudrate in self.BAUDRATES:
                length = 10
                print(f"running test with baudrate of '{baudrate}'")
                with self.subTest("baudrate"):
                    failures.append(self.length_check(10, self.MODULATION, baudrate))
            self.assertEqual(0, len(failures))
        else:
            raise unittest.SkipTest("not enabled in test config")





def modem_suite():
    suite = unittest.TestSuite()
    suite.addTest(ModemTest(f"test_short_message"))
    suite.addTest(ModemTest(f"test_medium_message"))
    suite.addTest(ModemTest(f"test_long_message"))
    return suite

