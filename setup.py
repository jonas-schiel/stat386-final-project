from setuptools import setup, find_packages

setup(
    name='my_package',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'requests',
        'beautifulsoup4',
        'matplotlib',
        'seaborn',
        'streamlit'
    ],
    author='Your Name',
    author_email='your.email@example.com',
    description='Economic and election data analysis package',
    python_requires='>=3.8',
)