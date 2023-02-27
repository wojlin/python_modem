import unittest
import subprocess
import os
import glob
import os

from test_utils import create_random_text


class ModemTest(unittest.TestCase):
    MODEM_TYPE = ""
        
    def setUp(self) -> None:
        self.test_path = os.path.dirname(os.path.realpath(__file__)) + "/"
        self.temp_path = self.test_path + "temp/"
        self.program_path = f"{'/'.join(self.test_path.split('/')[:-2])}/main.py"

    def test_basic(self):
        text = create_random_text(5)
        print(text)
        print(self.test_path)
        print(self.program_path)
        
        out_wav_name = f"{self.temp_path}{self.MODEM_TYPE}.wav"
        out_txt_name = f"{self.temp_path}{self.MODEM_TYPE}.txt"
        
        print("launching modulation...")
        
        command = f'python3 {self.program_path} modulate -m {self.MODEM_TYPE} --i "{text}" -o {out_wav_name}'.split()

        p = subprocess.Popen(command, shell=False)
        p.wait()
        
        print("launching demodulation...")
        
        command = f'python3 {self.program_path} demodulate -m {self.MODEM_TYPE} --i {out_wav_name} -o {out_txt_name}'.split()
        p = subprocess.Popen(command, shell=False)
        p.wait()
        
        print("comapraing modulated data with demodulated...")
        
        with open(out_txt_name) as f:
            content = f.read()
            print(f'original text: "{text}"')
            print(f"received text: {content}")
            self.assertEqual(f'"{text}"', content)


def modem_suite(modem_name: str):
    suite = unittest.TestSuite()
    ModemTest.MODEM_TYPE = modem_name
    suite.addTest(ModemTest(f"test_basic"))
    return suite


def prepare_test_env():
    test_path = os.path.dirname(os.path.realpath(__file__)) + "/"
    temp_path = self.test_path + "temp/"
    
    files = glob.glob(temp_path)
    for f in files:
        os.remove(f)
        print(f"removed {f} from temp!")
        
    print("test env prepared!")
    

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(modem_suite("ASK"))