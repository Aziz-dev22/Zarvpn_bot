# setup.py
from setuptools import setup, find_packages

setup(
    name="ZarVPN",
    version="1.0.0",
    author="Aziz",
    description="ربات تلگرام و وب‌پنل مدیریت هوشمند اتصال به X-UI سنایی و مرزبان",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "aiogram>=3.0.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.22.0",
        "jinja2>=3.1.2",
        "python-multipart>=0.0.6",
        "sqlalchemy>=2.0.0",
        "aiosqlite>=0.19.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.8.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
