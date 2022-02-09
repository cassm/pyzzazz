# Pyzzazz
### A python based light art control server

This project allows control of arbitrary numbers and types of fixtures from arbitrary numbers and types of controllers. Essentially, I got sick of writing the same five scripts every time I built something, and finally got around to generalising things

## Getting Started

Configuration is performed via a json file conf/conf.json. The syntax for this is slightly opaque, but a configurator will be forthcoming.
Palettes are read from the palettes/ directory. They need to be .bmp files, and are read horizontally along the top row

In order to launch the server, just run pyzzazz.py.

If you have a controller specified with type=gui pyzzazz will launch a TCP server and connect to any correctly configured instances. In order to launch the actual tkinter-based gui controller, run gui_controller_launcher.py. Because the communication is taking place over websockets, so with a bit of elbow grease you should be able to get a gui working on any device on the network. The packet format is specified (implicitly) in common/packet-handler.py. A protocol specification will be, again, forthcoming.

If you have a sender specified with type=opc and is_simulator=true, pyzzazz will generate layout files and launch the open pixel control gl_server, which will simulate the led fixtures which send to it

Power limiting is supported for LED fixtures. If the fixture is specified with a "power_budget" argument (in watts), pyzzazz will estimate the power consumption of a given frame and downscale it if necessary to avoid overdraw.

### Installing

This project runs under Python 3.6 and above. Use of pip and virtualenv is recommended.
Assuming you have the above installed, you can get started using the following steps under linux or macOS. These are largely generic instructions.

    # clone the repository
    git clone https://github.com/cassm/pyzzazz.git pyzzazz
    cd pyzzazz

    # create and activate the virtual environment
    virtualenv venv
    venv/bin/activate

    # install the python dependencies
    pip3 install -r requirements.txt

    # initialise and update the git submodules (currently openpixelcontrol)
    git submodule init
    git submodule update

    # run!
    python3 pyzzazz.py

the pixel position and colour information are served as JSON at localhost:5001/position and localhost:5001/colour respectively.

## Authors

* **Cass May** - Most of it

* **Vic Williams** - [Active contributor](github.com/pixelherd)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
