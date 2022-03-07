# Pyzzazz
### A python based light art control server

This project allows control of arbitrary numbers and types of fixtures from arbitrary numbers and types of controllers. Essentially, I got sick of writing the same five scripts every time I built something, and finally got around to generalising things

## Getting Started

Configuration is performed via a json file conf/conf.json. The syntax for this is slightly opaque, but a configurator will be forthcoming.
Palettes are read from the palettes/ directory. They need to be .bmp files, and are read horizontally along the top row

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

    # run!
    python3 pyzzazz.py

the pixel position and colour information are served as JSON at localhost:5001/position and localhost:5001/colour respectively.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
