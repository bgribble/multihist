import setuptools

setuptools.setup(
    name="multihist",
    version="0.1.0",
    author="Bill Gribble",
    author_email="grib@billgribble.com",
    description="Manage history for multiople concurrently-open BASH shells",
    url="https://github.com/bgribble/multihist",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'multihist=multihist.multihist:main'
        ]
    },
)
