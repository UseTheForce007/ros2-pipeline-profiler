from setuptools import setup, find_packages

setup(
    name="ros2_pipeline_profiler_analyzer",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ros2-pipeline-profiler-analyzer=ros2_pipeline_profiler_analyzer.cli:main",
        ],
    },
)
