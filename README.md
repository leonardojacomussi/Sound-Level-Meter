# Sound-Level-Meter: Sonômetro programado em Python para sistemas embarcados (SBC - Single Board Computer)
Este projeto é fruto do trabalho de conclusão de curso que desenvolvi durante a graduação do curso de [Engenharia Acústica][EAC], pela Universidade Federal de Santa Maria ([UFSM][ufsmsite]). 

Neste repositório contém os *software* implementados em Python 3 com as ferramentas típicas de um sonômetro (ou Medidor de Nível de Pressão Sonora - MNPS), desde a análise do NPS global a NPS em banda larga (em versão futura, contemplará medições de respostas impulsivas para o cálculo do tempo de reverberação de salas), contendo além do processamento digital de sinais de áudio (*back-end*), um completo conjunto de interfaces gráficas que facilitam a configuração e acesso aos dados medidos.

Além do *software*, o projeto conta com um conjunto de *hardware* que contempla toda a cadeia de sinais de um MNPS, como microfone de eletreto, conversor analógico-digital (placa de áudio), unidade de processamento (sistema embarcado) e visor (*display touch screen*).

## Uso
O projeto foi especialmente otimizado pala ser compilado em sistemas embarcados com capacidade reduzida de processamento, porém deve funcionar perfeitamente em computadores convencionais como *desktops* e *notebook*, desde que estes possuam placa de áudio, microfone e visor. Neste caso, recomendo utilizar o Anaconda, distribuição gratuita e de código aberto da linguagem de programação Python.

### Configurando
Para usar os *software* basta baixar os arquivos, instalar as dependências e fazer os seguintes ajustes:
- *default.py* --> Neste arquivo você deve encontrar o(s) dispositivo(s) de aúdio conectados ao sistema embarcado ou computador e configurá-lo na variável *device*. Do mesmo modo, deve colocar o número dos canais de entrada e saída nas variáveis *inputChannels* e *outChannels*. Por fim, configure corretamente a taxa de amostragem na variável *samplingRate*. Após terminar as configurações, salve o arquivo.

- *startMNPS.py* -->Execute este arquivo para rodar o *software*.

## Os sistema embarcados testados foram:
* [Tinker Board S][TinkerB] - Com o sistema operacional Tinker [Board Debian Stretch-V2.1.11][TinkerOS]
* [Raspberry Pi 4 B (4gb)][Rpi4] - Com o sistema operacional [Raspbian Buster versão 2020-02-13][Raspbian]
* [Raspberry Pi 4 B+][Rpi3] - Com o sistema operacional [Raspbian Buster versão 2020-02-13][Raspbian]


## Protótipos
De modo geral, os protótipos são constituídos dos componentes de *hardware* contidos na tabela a seguir:

|              Componente         |                       Modelo                   | Protótipo Tinker Board | Protótipo Rpi 4 | Protótipo Rpi 3    |
|:-------------------------------:|:----------------------------------------------:|:----------------------:|:---------------:|:------------------:|
|                                 |     ASUS Tinker Board                          |              x         |                 |                    |
|        Sistema embarcado        |     Raspberry Pi 4 B 4 gb                      |                        |          x      |                    |
|                                 |     Raspberry Pi 3 B+                          |                        |                 |          x         |
|     Conversor analógico-digital |     C-Media CM6206                             |              x         |          x      |                    |
|                                 |     ORICO SC2                                  |                        |                 |          x         |
|     Microfone                   |     Dayton Audio iMM-6                         |              x         |          x      |                    |
|                                 |     MOVO MA1000                                |                        |                 |          x         |
|     Power bank                  |     Fresh ’n Rebel 12000mAh                    |              x         |          x      |          x         |
|                                 |     Osoyoo de 5 polegadas                      |              x         |                 |                    |
|     Display touch screen        |     Elecrow de 5 polegadas                     |                        |          x      |                    |
|                                 |     3,5 polegadas                              |                        |                 |          x         |
|     Cabo de áudio               |     Plug P2 fêmea para 2 (dois) plugs P2 macho |              x         |          x      |          x         |
|     Cabos USB                   |     USB-A para USB-A e USB-A para micro USB    |              x         |          x      |          x         |


# Versões
- Branch: **Master** --> versão completa do *software* contendo níveis de pressão sonora em banda larga em tempo real e futuramente método de cálculo do tempo de reverberação.

- Branch: **Simple-version** --> versão simples do *software* contendo apenas níveis de pressão sonora em tempo real, no entando, ao optar em salvar a medição, é feito a filtragem do sinal medido em bandas de 1/3 de oitava.


# Dependências
- Python 3.7
- PyQt5
- PyQtGraph
- PyAudio
- PyTTa
- NumPy
- SciPy
- PyFilterBank
- Acoustics
- XlsxWriter

# Contato
- Autor: Leonardo Jacomussi
  - [LinkedIn][LinkedIn_Leo]
  - [ResearchGate][ResearchGate_Leo]

- Orientador: William D'Andrea Fonseca
  - [LinkedIn][LinkedIn_Will]
  - [ResearchGate][ResearchGate_Will]

# Referências
https://www.researchgate.net/publication/344435460_Raspberry_Pi_A_Low-cost_Embedded_System_for_Sound_Pressure_Level_Measurement


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
