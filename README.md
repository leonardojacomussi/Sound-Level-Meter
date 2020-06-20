# Sound-Level-Meter: Sonômetro programado em Python para sistemas embarcados (SBC - Single Board Computer)
Este projeto é fruto do trabalho de conclusão de curso que desenvolvi durante a graduação do curso de [Engenharia Acústica][EAC], pela Universidade Federal de Santa Maria ([UFSM][ufsmsite]). 

Nste repositório contém os *software* implementados em Python 3 com as ferramentas típicas de um sonômetro (ou medidor de nível de pressão sonora - MNPS), desde a análise espectral do NPS em banda larga a medição de resposta impulvia para o cálculo do tempo de reverberação de uma sala, contendo além do processamento digital de sinais de áudio (*back-end*), um completo conjunto de interfaces gráficas que facilitam a configuração e acesso aos dados medidos.

Além do *software*, o projeto conta com um conjunto de *hardware* que contempla toda a cadeia de sinais de um MNPS, como microfone de eletreto, conversor analógico-digital (placa de áudio), unidade de processamento (sistema embarcado) e visor (*display touch screen*).

## Uso
O projeto foi especialmente otimizado pala ser compilado em sistemas embarcados com capacidade reduzida de processamento, porém deve funcionar perfeitamente em computadores convencionais como *desktops* e *notebook*, desde que estes possuam placa de áudio, microfone e visor. Neste caso, recomendo utilizar o Anaconda, distribuição gratuita e de código aberto da linguagem de programação Python.

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

# Referências
Citar artigo Internoise 2020, ResearchGate e Llinkedin.


[EAC]: <https://www.eac.ufsm.br/>
[ufsmsite]: <https://www.ufsm.br/>
[TinkerB]: <https://www.asus.com/Single-Board-Computer/Tinker-Board-S/#tinker-board-chart>
[TinkerOS]: <https://www.asus.com/Single-Board-Computer/Tinker-Board-S/HelpDesk_Download/>
[Rpi4]: <https://www.raspberrypi.org/products/raspberry-pi-4-model-b/>
[Rpi3]: <https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/>
[Raspbian]: <https://www.raspberrypi.org/downloads/raspberry-pi-os/>
