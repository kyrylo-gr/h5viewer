import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='h5viewer',
    version="0.4.0",
    author="LKB-OMQ",
    author_email="cryo.paris.su@gmail.com",
    description="Viewer for hdf5 files created by labmate",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kyrylo-gr/h5viewer",
    # py_modules=['h5viewer'],
    package_dir={'': 'src'},
    # packages=['labmate'],
    packages=setuptools.find_packages(where='src', exclude=['tests', 'tests.*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points={"console_scripts": ["h5viewer = h5viewer.main:main"]},
    install_requires=[
        "PyQt6",
        "labmate",
    ],
)
