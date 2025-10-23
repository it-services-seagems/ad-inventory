import setuptools

with open('README.rst', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='KlAkOAPI',
    version='1.0.0.0',
    license='LICENSE',
    author='Kaspersky Lab',
    description='Wrapper library for interacting Kaspersky Security Center (aka KSC) server with KSC Open API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['KlAkOAPI'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License 2.0 (Apache-2.0)',
    ],
    python_requires='>=3.6',
    install_requires=['requests','pywin32 >= 1.0 ; platform_system=="Windows"'],
    url="http://kaspersky.com"
)