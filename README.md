# Python Modem

## Description
python modem is a tool for converting digital data into sound waves using various modulations.
this tool also makes it possible to demodulate this data back into a binary form

in addition, it can also analyze modulated and demodulated sound waves and present them in a user-friendly graphic form

this program can also be used as a chatbot working via terminal or rest api

## Info

| Modulation Type | implemented | Max reliable baudrate |
|---|---|---|
| ASK | ✅YES | 2000bps |
| 4-ASK | ❌NO | N/A |
| FSK | ❌NO | N/A |
| BPSK | ❌NO | N/A |
| QPSK | ❌NO | N/A |

## Installing

```commandline
git clone git@github.com:wojlin/python_modem.git
cd python_modem
pip install -r requirements.txt
```

install PortAudio library before launching this project for the first time
```commandline
sudo apt-get install libportaudio2 ; sudo apt-get install libasound-dev
```

## Usage

modulate data given in parameters into sound wave using ASK modulation
```commandline
python3 main.py modulate -m ASK --i "abcdefg" -o "<path>.wav"
```

modulate data given in parameters into sound wave using ASK modulation and play it
```commandline
python3 main.py modulate -m ASK --i "abcdefg" -o "<path>.wav" -p
```

demodulate sound file using ASk demodulation and save its output to text file
```commandline
python3 main.py demodulate -m ASK --i "<path>.wav" -o "<path>"
```

launch peer to peer communication program
```commandline
python3 peer_to_peer.py
```

view all possible commands by using:
```commandline
python3 main.py --help
```
