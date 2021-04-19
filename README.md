# A Sound Level Meter programmed in Python for Single Board Computer (SBC)
This project is the result of the course completion work that I developed during the undergraduate course in [Acoustical Engineering][EAC] at the Federal University of Santa Maria ([UFSM][ufsmsite]). 

In this repository some information about the sound level meter prototypes developed and presented in the conference paper [*Raspberry Pi: A Low-cost Embedded System for Sound Pressure Level Measurement*][ArtigoInternoise]. The hardware sets for each prototype and a tutorial on how to install the software dependencies are briefly presented.

In addition to the software, the project has a set of hardware that includes the entire signal chain of an SLM, such as an electret microphone, analog-digital converter (sound card), processing unit (embedded system) and display (touch display) screen).

## Software
The PySLM package was developed in Python 3 and is located in [this repository][pyslm] (access for more information).

The project was specially optimized to be compiled in embedded systems with reduced processing capacity, but it should work perfectly in conventional computers such as desktops and notebooks, as long as they have an audio card, microphone and display. In this case, I recommend using Anaconda, a free and open source distribution of the Python programming language.

## The tested embedded systems were:
* [Tinker Board S][TinkerB] - With the [Tinker Board Debian Stretch-V2.1.11][TinkerOS] operating system
* [Raspberry Pi 4 B (4gb)][Rpi4] - With the [Raspbian Buster versão 2020-02-13][Raspbian] operating system
* [Raspberry Pi 4 B+][Rpi3] - With the [Raspbian Buster versão 2020-02-13][Raspbian] operating system


## Prototypes
In general, prototypes are made up of the hardware components contained in the following table:

|              Component          |                       Model                    | Prototype Tinker Board | Prototype Rpi 4 | Prototype Rpi 3    |
|:-------------------------------:|:----------------------------------------------:|:----------------------:|:---------------:|:------------------:|
|                                 |     ASUS Tinker Board                          |              x         |                 |                    |
|        Embedded system          |     Raspberry Pi 4 B 4 gb                      |                        |          x      |                    |
|                                 |     Raspberry Pi 3 B+                          |                        |                 |          x         |
|     Analog-to-digital converter |     C-Media CM6206                             |              x         |          x      |                    |
|                                 |     ORICO SC2                                  |                        |                 |          x         |
|     Microphone                  |     Dayton Audio iMM-6                         |              x         |          x      |                    |
|                                 |     MOVO MA1000                                |                        |                 |          x         |
|     Power bank                  |     Fresh ’n Rebel 12000mAh                    |              x         |          x      |          x         |
|                                 |     5-inch Osoyoo                              |              x         |                 |                    |
|     Display touch screen        |     5-inch elecrow                             |                        |          x      |                    |
|                                 |     3.5 inches                                 |                        |                 |          x         |
|     Audio cable                 |     Female P2 plug for 2 (two) male P2 plugs   |              x         |          x      |          x         |
|     USB Cables                  |     USB-A to USB-A and USB-A to micro USB      |              x         |          x      |          x         |


# Dependencies
As in Linux operating systems there may be several versions of Pyhton compilers, eventually package versioning conflicts may occur. One way to get around this problem is to create a virtual environment within the operating system, it will contain only a Python compiler and also only one version of each package. In an operating system it is possible to create numerous virtual environments and work in each of them with different versions of Python packages and compilers without conflicts.

The software dependencies will be installed within a virtual environment, facilitating the work environment. For this, considering that version 3.7 or higher of the Python compiler is already installed in the operating system, the next step is to check the existence of the PyPI package manager, with the following command: *pip3.8 -V*. If there is a version 3.7 or higher it will not be necessary to install it, otherwise, with the *sudo apt-get install python3.8-pip* command it is possible to install the PyPI package manager. To start a virtual environment the following steps must be followed:

1 - Install the virtualenv package:

    $ sudo apt-get install virtualenv
    
2 - Create a virtual environment with the following command, where '/usr/local/bin/python3.8' is the directory of the Python 3.8 compiler and slm is the name of the virtual environment folder, both of which can be changed in the highlighted arguments according to the Python installation location or name of the project you want to start:

    $ virtualenv slm --python='/usr/local/bin/python3.8'
    
3 - To open the created environment, execute the following command::

    $ source slm/bin/activate
    
4 - To leave the virtual environment, use the command:
    
    $ deactivate

With the virtual environment created, it is possible to start the installation of the necessary packages for the operation of the [PySLM][pyslm] package.

### Python 3.8
Installation:

    $ sudo apt-get install build-essential checkinstall
    $ sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev
    $ cd /usr/src
    $ sudo wget https://www.python.org/ftp/python/3.8.6/Python-3.8.6.tgz
    $ sudo tar xzf Python-3.8.6.tgz
    $ cd Python-3.8.6
    $ sudo ./configure –enable-optimizations
    $ sudo make altinstall
  
### libatlas-base-dev
Installation:

    $ sudo apt-get install libatlas-base-dev

### libhdf5-serial-dev
Installation:

    $ sudo apt-get install libhdf5-serial-dev
    
### gfortran
Installation:

    $ sudo apt-get install gfortran
    
### gcc
Installation:

    $ sudo apt-get install gcc
 
### PortAudio
Installation:

    $ sudo apt-get install portaudio19-dev
    
### cffi
Installation:

    $ pip install cffi
    
### cython
Installation:

    $ pip install cython
    
### numpy
Installation:

    $ pip install numpy
    
### pandas
Installation:

    $ pip install pandas
    
### scipy
Installation:

    $ pip install scipy
    
### matplotlib
Installation:

    $ pip install matplotlib
    
### h5py
Installation:

    $ pip install h5py
    
### sounddevice
Installation:

    $ pip install sounddevice
    
### pyqtgraph
Installation:

    $ pip install pyqtgraph
    
### sip
Installation:

    $ pip install sip
    
### xlsxwriter
Installation:

    $ pip install xlsxwriter
    
### pyqt5
Installation:

    $ sudo apt-get install build-essential
    $ sudo apt-get install libfontconfig1
    $ sudo apt-get install mesa-common-dev
    $ sudo apt-get install libglu1-mesa-dev -y
    $ sudo apt-get install qt-qdefault
    $ sudo apt-get install qt5-qmake
    $ pip install PyQt-builder
    $ pip install PyQt-sip
    $ pip install pyqt5

### pyslm
Installation:

    $ pip install git+https://github.com/leonardojacomussi/PySLM@main

# Contact
- Author: Leonardo Jacomussi
  - [LinkedIn][LinkedIn_Leo]
  - [ResearchGate][ResearchGate_Leo]

- Advisor: William D'Andrea Fonseca
  - [LinkedIn][LinkedIn_Will]
  - [ResearchGate][ResearchGate_Will]

# See more
[PySLM - Pythonic Sound Level Meter][pyslm]

[*Raspberry Pi: A Low-cost Embedded System for Sound Pressure Level Measurement*][ArtigoInternoise]

[*Tutorial: configuração de dispositivos de áudio no Raspberry Pi – Parte 1*][Artigo_acustica1]

[*Tutorial: configuração de dispositivos de áudio no Raspberry Pi – Parte 2*][Artigo_acustica2]



[EAC]: <https://www.eac.ufsm.br/>
[ufsmsite]: <https://www.ufsm.br/>
[TinkerB]: <https://www.asus.com/Single-Board-Computer/Tinker-Board-S/#tinker-board-chart>
[TinkerOS]: <https://www.asus.com/Single-Board-Computer/Tinker-Board-S/HelpDesk_Download/>
[Rpi4]: <https://www.raspberrypi.org/products/raspberry-pi-4-model-b/>
[Rpi3]: <https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/>
[Raspbian]: <https://www.raspberrypi.org/downloads/raspberry-pi-os/>
[LinkedIn_Leo]: <https://www.linkedin.com/in/leonardo-jacomussi-6549671a2>
[ResearchGate_Leo]: <https://www.researchgate.net/profile/Leonardo_Jacomussi_Pereira_De_Araujo>
[LinkedIn_Will]: <https://www.linkedin.com/in/william-fonseca>
[ResearchGate_Will]: <https://www.researchgate.net/profile/William_Fonseca3>
[ArtigoInternoise]: <https://www.researchgate.net/publication/344435460_Raspberry_Pi_A_Low-cost_Embedded_System_for_Sound_Pressure_Level_Measurement>
[Artigo_acustica1]: <https://www.researchgate.net/publication/345948469_Tutorial_configuracao_de_dispositivos_de_audio_no_Raspberry_Pi_-_Parte_1>
[Artigo_acustica2]: <https://www.researchgate.net/publication/345948561_Tutorial_configuracao_de_dispositivos_de_audio_no_Raspberry_Pi_-_Parte_2>
[pyslm]: <https://github.com/leonardojacomussi/PySLM>
