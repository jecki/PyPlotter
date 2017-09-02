from setuptools import setup

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(name="JyPlotter",
      version="0.9.5",
      description="Graph plotting library with backends for different GUIs",
      long_description=long_description,
      author="Eckhart Arnold",
      license="MIT",
      url="https://github.com/jecki/PyPlotter",
      author_email="eckhart.arnold@posteo.de",
      packages=["PyPlotter"],
      keywords='Plotting Graph Simplex Cartesian',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Topic :: Scientific/Engineering :: Visualization',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: IronPython',
          'Programming Language :: Python :: Implementation :: Jython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Programming Language :: Python :: Implementation :: Stackless'
      ]
      )

