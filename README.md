# Pyzzazz
### A python based light art control server

This project allows control of arbitrary numbers and types of fixtures from arbitrary numbers and types of controllers. Essentially, I got sick of writing the same five scripts every time I built something, and finally got around to generalising things

## Getting Started

Configuration is performed via a json file conf/conf.json. The syntax for this is slightly opaque, but a configurator will be forthcoming.
Palettes are read from the palettes/ directory. They need to be .bmp files, and are read horizontally along the top row

In order to launch the server, just run pyzzazz.py. For a gui control box, run gui_controller_launcher.py. These communicate via websockets, so with a bit of elbow grease you should be able to get a gui working on any device on the network. The packet format is specified (implicitly) in common/packet-handler.py. A protocol specification will be, again, forthcoming.

### Prerequisites

This project runs under Python 3.6 and above

You will need the following libraries:
- pyserial (NOT the package called serial, which has a clashing namespace)
- tkinter
- imageio
- bitarray

### Installing

Just download, install the libraries, and run!

## Authors

* **Cass May** - Most of it

* **Vic Williams** - [Active contributor](github.com/pixelherd)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
