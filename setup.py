from setuptools import setup, find_packages

setup(
    name='cm600_exporter',
    version='0.0.2',
    description='Netgear CM600 Collector for Prometheus',
    author='Aleks Bunin',
    author_email='b@compuix.com',
    license='proprietary',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    data_files=[('', ['src/cm600_exporter/tests/page.html'])],
    install_requires=[
        'requests',
        'beautifulsoup4',
        'prometheus_client',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': ['cm600_exporter=cm600_exporter.__main__:main'],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
