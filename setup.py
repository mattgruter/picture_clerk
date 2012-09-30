from distutils.core import setup

setup(
    name='PictureClerk',
    version='0.1dev',
    author='Matthias Gruter',
    author_email='matthias@grueter.name',
    packages=['picture_clerk','picture_clerk.test'],
    scripts=['bin/pic'],
    url='https://github.com/mgrueter/picture_clerk',
    license='LICENSE.txt',
    description='The little helper for your picture workflow.',
    long_description=open('README.txt').read(),
    #install_requires=[
    #    "pyexiv2 >= 0.3",
    #    "paramiko >= 1.7.3" 
    #],
)
