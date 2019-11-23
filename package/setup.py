from setuptools import setup

setup(
    name="cinder_exporter",
    version="1.0.0",
    description="Exports to Prometheus Cinder metrics",
    url="https://github.com/loko-loko/openstack-cinder-exporter.git",
    author="loko-loko",
    author_email="loko-loko@github.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.8",
    ],
    packages=["cinder_exporter"],
    include_package_data=True,
    install_requires=["loguru", "prometheus_client", "openstacksdk", "urllib3"],
    entry_points={
        "console_scripts": [
            "cinder_exporter=cinder_exporter.__main__:main",
        ]
    },
)
