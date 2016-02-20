PyPlotter / JyPlotter - A Python / Jython Plotting Library
==========================================================

Version: 0.9.4 (February, 19th 2015)

(c) 2004 Eckhart Arnold under the MIT License (opensource.org/licenses/MIT)


Author: Eckhart Arnold

Email:  eckhart.arnold@posteo.de

Web:    http://eckhartarnold.de

Source: https://github.com/jecki/PyPlotter

Manual: http://pythonhosted.org/JyPlotter/



Description
-----------

PyPlotter is a Python package for plotting graphs and diagrams with very
small footprint. Possible use cases for PyPlotter still are: 

- you need a plotting package that works with jython in the java virtual
  machine

- you need a lightweight graph plotting package with small footprint
  
- you need a plotting package that can easily be adapted to some obscure
  graphics library or GUI-toolkit that is not supported by matplotlib

- you need a plotting package without any particular C-library dependencies

- [matplotlib](http://matplotlib.org/) is just too large for you

PyPlotter allows plotting on linear and logarithmic scales. Apart from
that it contains classes for plotting simplex diagrams, such as are
used in evolutionary game theory for example.

Through its own device driver PyPlotter can easily be adapted to
different graphical user interfaces or output devices. This means that
the same plotting subroutines can be used in a Jython applet in
conjunction with the Java AWT or in a standalone application utilizing
the wxWidgets, gtk or qt tookit.


Installation Instructions
-------------------------

The easiest way to install PyPlotter / JyPlotter is with the `pip`-Installer
from Python package index:

    [sudo] pip install JyPlotter
    
Attention: It needs to be `JyPlotter` not `PyPlotter` because there seems to
exist another package with the same name in PyPi.

Alternatively, you can also download the PyPlotter subfolder and place it
inside your project folder. Importing PyPlotter works just the same way
as described in the [manual](http://eckhartarnold.de/apppages/onlinedocs/PyPlotter_Doc/PyPlotter_Doc.html).

