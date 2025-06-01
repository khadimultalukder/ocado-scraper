from setuptools import setup, find_packages

setup(
    name="ocado_scraper",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["requests", "beautifulsoup4"],
    description="Multithreaded Ocado scraper with retry and logging",
    author="Your Name",
    entry_points={
        "console_scripts": [
            "ocado-scrape = main:main",
        ],
    }
)
