<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->

<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
<h3 align="center">Data Analysis and Visualization Pipeline</h3>

  <p align="center">
    A comprehensive backend system for natural language query processing, data analysis, and visualization generation
    <br />
    <a href="https://github.com/RecceLabTechies/Backend"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/RecceLabTechies/Backend">View Demo</a>
    &middot;
    <a href="https://github.com/RecceLabTechies/Backend/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/RecceLabTechies/Backend/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#architecture">Architecture</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#core-components">Core Components</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
    <li><a href="#mongodb-integration">MongoDB Integration</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

This project provides an end-to-end pipeline for processing natural language queries about data, selecting appropriate datasets, analyzing the data, and generating meaningful visualizations or textual reports. The system uses Flask to expose API endpoints and leverages LLM models via Ollama for intelligent query processing.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Architecture

The system follows a modular architecture divided into four main components:

1. **Query Processing** - Validates and classifies user queries
2. **Data Processing** - Selects and processes relevant JSON data
3. **Regular Generation** - Creates descriptions and chart data visualizations
4. **Report Generation** - Produces comprehensive analytical reports

#### Pipeline Flow

```
User Query → Query Validation → Query Classification → Data Selection → Data Processing → Output Generation
```

Where Output Generation can be:

- Textual descriptions
- Chart visualizations
- Comprehensive reports

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

- ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
- ![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
- ![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
- ![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)
- ![Matplotlib](https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black)
- ![scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)
- ![LangChain](https://img.shields.io/badge/LangChain-%23008080.svg?style=for-the-badge&logo=LangChain&logoColor=white)
- Ollama (Local LLM deployment)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

Follow these instructions to set up the project locally.

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Ollama for local LLM deployment

### Installation

1. Clone the repository
   ```sh
   git clone https://github.com/RecceLabTechies/Backend.git
   ```
2. Create a virtual environment
   ```sh
   python -m venv venv
   ```
3. Activate the virtual environment

   ```sh
   # Linux/Mac
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

4. Install the required dependencies
   ```sh
   pip install -r requirements.txt
   ```
5. Install the package in development mode
   ```sh
   pip install -e .
   ```
6. Install Ollama and the required models using the modelfiles in the `models/` directory
   ```sh
   # Example (after installing Ollama)
   ollama create query-classifier -f models/query_classifier.modelfile
   ollama create json-selector -f models/json_selector.modelfile
   ollama create json-processor -f models/json_processor.modelfile
   ollama create description-generator -f models/description_generator.modelfile
   ollama create chart-data-generator -f models/chart_data_generator.modelfile
   ollama create report-generator -f models/report_generator.modelfile
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Usage

### Running the Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:5152`.

### Making API Requests

```python
import requests
import json

response = requests.post(
    "http://localhost:5152/api/query",
    headers={"Content-Type": "application/json"},
    data=json.dumps({"query": "Show me a chart of monthly revenue"})
)

result = response.json()
print(result)
```

### Running from Command Line

```bash
python pipeline.py "Show me a chart of monthly revenue"
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- PROJECT STRUCTURE -->

## Project Structure

```
.
├── app.py                      # Flask application entry point
├── pipeline.py                 # Main pipeline implementation
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup file
├── mypackage/                  # Main package directory
│   ├── __init__.py             # Package initialization
│   ├── a_query_processor/      # Query processing modules
│   │   ├── __init__.py
│   │   ├── query_classifier.py
│   │   └── query_validator.py
│   ├── b_data_processor/       # Data processing modules
│   │   ├── __init__.py
│   │   ├── json_processor.py
│   │   └── json_selector.py
│   ├── c_regular_generator/    # Output generation modules
│   │   ├── __init__.py
│   │   ├── chart_data_generator.py
│   │   └── description_generator.py
│   └── d_report_generator/     # Report generation modules
│       ├── __init__.py
│       ├── generate_analysis_queries.py
│       ├── report_generator.py
│       └── truncated_pipeline.py
├── models/                     # LLM model definitions
│   ├── chart_data_generator.modelfile
│   ├── description_generator.modelfile
│   ├── json_processor.modelfile
│   ├── json_selector.modelfile
│   ├── query_classifier.modelfile
│   └── report_generator.modelfile
├── data/                       # Data files
│   ├── cleaned_Adjusted_Ad_Campaign_Performance_Data.json
│   └── cleaned_Banking_KPI_Data.json
└── tests/                      # Test suite
    ├── a_query_processor/
    ├── b_data_processor/
    ├── c_regular_generator/
    └── d_report_generator/
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CORE COMPONENTS -->

## Core Components

### a_query_processor

Handles the initial processing of user queries:

- `query_validator.py` - Ensures queries are valid and well-formed
- `query_classifier.py` - Categorizes queries into different types (description, chart, report, error)

### b_data_processor

Manages data selection and processing:

- `json_selector.py` - Determines which JSON dataset to use based on the query
- `json_processor.py` - Processes the selected JSON data to extract relevant information

### c_regular_generator

Generates standard outputs based on processed data:

- `description_generator.py` - Creates textual descriptions of data
- `chart_data_generator.py` - Produces chart data for visualization

### d_report_generator

Creates comprehensive reports:

- `report_generator.py` - Main entry point for report generation
- `generate_analysis_queries.py` - Generates sub-queries for comprehensive analysis
- `truncated_pipeline.py` - A modified pipeline for report sub-components

### Models

The system uses Ollama to run local LLM models for different pipeline stages:

- `query_classifier.modelfile` - Classifies queries by type
- `json_selector.modelfile` - Selects appropriate JSON files
- `json_processor.modelfile` - Processes JSON data
- `description_generator.modelfile` - Generates text descriptions
- `chart_data_generator.modelfile` - Generates chart data
- `report_generator.modelfile` - Creates reports

All models are based on Qwen2.5 with specific system prompts and parameters for each task.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->

## Roadmap

- [ ] Add support for more data formats beyond JSON
- [ ] Implement caching for improved performance
- [ ] Add more visualization types
- [ ] Create a front-end interface for easier query submission
- [ ] Expand test coverage

See the [open issues](https://github.com/RecceLabTechies/Backend/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->

## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

RecceLabTechies - [@RecceLabTechies](https://github.com/RecceLabTechies)

Project Link: [https://github.com/RecceLabTechies/Backend](https://github.com/RecceLabTechies/Backend)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [Ollama Project](https://ollama.ai/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Best-README-Template](https://github.com/othneildrew/Best-README-Template)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/RecceLabTechies/Backend.svg?style=for-the-badge
[contributors-url]: https://github.com/RecceLabTechies/Backend/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/RecceLabTechies/Backend.svg?style=for-the-badge
[forks-url]: https://github.com/RecceLabTechies/Backend/network/members
[stars-shield]: https://img.shields.io/github/stars/RecceLabTechies/Backend.svg?style=for-the-badge
[stars-url]: https://github.com/RecceLabTechies/Backend/stargazers
[issues-shield]: https://img.shields.io/github/issues/RecceLabTechies/Backend.svg?style=for-the-badge
[issues-url]: https://github.com/RecceLabTechies/Backend/issues
[license-shield]: https://img.shields.io/github/license/RecceLabTechies/Backend.svg?style=for-the-badge
[license-url]: https://github.com/RecceLabTechies/Backend/blob/master/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png

## MongoDB Integration

The LLM Backend is now integrated with MongoDB for data persistence. Here's what you need to know:

### MongoDB Connection

- The application automatically connects to MongoDB using the environment variables from docker-compose.yml
- Default connection string: `mongodb://root:example@mongodb:27017/`
- Default database name: `test_database`

### Collections

The following collections are pre-configured:

- `users`
- `campaign_performance`
- `prophet_predictions`

### Endpoints

- `GET /api/health` - Check if the application and database are healthy
- `GET /api/collections` - List available MongoDB collections

### Testing Connection

To test the MongoDB connection:

```bash
python -m tests.test_mongodb
```
