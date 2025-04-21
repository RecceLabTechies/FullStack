# README

<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->

<a id="readme-top"></a>

<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">

<h3 align="center">Marketing Analytics Platform</h3>

  <p align="center">
    A comprehensive marketing analytics platform with AI-powered insights, interactive dashboards, and predictive capabilities.
    <br />
    <a href="https://github.com/RecceLabTechies/LLM-Powered-Dashboard"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/RecceLabTechies/LLM-Powered-Dashboard">View Demo</a>
    &middot;
    <a href="https://github.com/RecceLabTechies/LLM-Powered-Dashboard/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/RecceLabTechies/LLM-Powered-Dashboard/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
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
    <li><a href="#key-features">Key Features</a></li>
    <li><a href="#development">Development</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

This project is a modern marketing analytics platform designed with a microservices architecture, featuring:

- **Interactive Dashboards**: Visualize marketing performance across channels, age groups, and countries
- **Predictive Analytics**: Machine learning powered forecasting of revenue, ROI, and other key metrics
- **AI-Powered Insights**: Natural language query processing for generating custom reports and visualizations
- **Data Management**: Upload, edit, and analyze marketing campaign data

The application leverages a robust tech stack with Next.js for the frontend, Flask for backend services, MongoDB for data storage, and specialized AI components for advanced analytics capabilities.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

- [![Next][Next.js]][Next-url]
- [![React][React.js]][React-url]
- [![Python][Python.org]][Python-url]
- [![Flask][Flask.com]][Flask-url]
- [![MongoDB][MongoDB.com]][MongoDB-url]
- [![TailwindCSS][TailwindCSS.com]][TailwindCSS-url]
- [![Docker][Docker.com]][Docker-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

To get a local copy up and running, follow these steps.

### Prerequisites

Make sure you have the following software installed:

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.8+ (for local backend development)
- Groq API key (for LLM functionality)

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/RecceLabTechies/LLM-Powered-Dashboard.git
   ```
2. Create a `.env` file in the root directory with your Groq API key:
   ```
   GROQ_API_KEY=your-groq-api-key
   ```
3. Make the startup script executable
   ```sh
   chmod +x start_app.sh
   ```
4. Start the application
   ```sh
   ./start_app.sh
   ```
5. The script will:
   - Check if Docker is running
   - Start all services (MongoDB, Backend API, Frontend, LLM Backend, Nginx)
   - Initialize MongoDB with sample data if needed
6. Access the application
   - Frontend UI: http://localhost:80
   - Backend API: http://localhost:80/api
   - LLM Backend: http://localhost:80/llm-api

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Usage

### Authentication

The platform includes a user authentication system with role-based access control:

- Login using email and password (sample credentials for local development)
- Role-based permissions for different dashboard features

### Dashboard

The main dashboard provides comprehensive marketing analytics:

- Key performance metrics (Revenue, ROI, Predicted Revenue)
- Performance breakdown by marketing channel
- Age group and country analysis
- Machine learning predictions visualizations

### LLM Query Processing

The AI-powered analytics engine allows for natural language queries:

- Ask questions about your data in plain English
- Receive automatically generated charts or text descriptions
- Generate comprehensive reports with multiple visualizations

### Data Management

Upload and manage your marketing campaign data:

- Import CSV files with campaign performance data
- Edit existing records
- Run ML predictions on new data

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- PROJECT STRUCTURE -->

## Project Structure

```
.
├── frontend/             # Next.js frontend application
│   ├── src/              # Source code
│   │   ├── app/          # Next.js app router pages
│   │   ├── components/   # UI components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── context/      # React context providers
│   │   ├── lib/          # Utility functions
│   │   └── api/          # API integration
├── backend/              # Flask API backend server
│   ├── app/              # Application code
│   │   ├── routes/       # API endpoints
│   │   ├── models/       # Data models
│   │   ├── services/     # Business logic
│   │   └── database/     # Database connections
├── llm-backend/          # LLM service backend
│   ├── app.py            # Main application entry
│   ├── pipeline.py       # Query processing pipeline
│   └── mypackage/        # ML and LLM utilities
├── mongodb-init/         # MongoDB initialization scripts
├── nginx/                # Nginx configuration
├── docker-compose.yml    # Docker compose configuration
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- KEY FEATURES -->

## Key Features

### Marketing Analytics Dashboard

The platform provides comprehensive marketing analytics with:

- **Revenue and ROI Metrics**: Track key performance indicators
- **Channel Analysis**: Compare performance across marketing channels
- **Audience Segmentation**: Analyze by age group and country
- **Cost Metrics Heatmap**: Visualize cost-effectiveness
- **Revenue vs. Ad Spend**: Track ROI and marketing efficiency

### Machine Learning Predictions

The platform includes ML-powered forecasting:

- **Revenue Predictions**: Time-series forecasting using Prophet models
- **ROI Projections**: Predicted return on investment
- **Performance Trends**: Identify upcoming trends in marketing effectiveness
- **User-Triggered ML**: Run predictions on demand from the dashboard

### AI-Powered Analytics

The LLM backend enables natural language analytics:

- **Query Classification**: Automatically determines if the request needs a chart, description, or report
- **Natural Language Processing**: Ask questions in plain English
- **Automated Visualization**: Generates appropriate charts based on queries
- **Comprehensive Reports**: Creates multi-section reports with visualizations and insights
- **Asynchronous Processing**: Handles complex queries with a job-based system

### Data Management

The platform provides tools for managing marketing data:

- **Data Upload Interface**: Import CSV files with campaign data
- **Data Editing**: Modify existing records
- **Data Filtering**: Focus on specific time periods or campaigns
- **Multi-dimension Analysis**: Compare across channels, age groups and countries

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- DEVELOPMENT -->

## Development

### Frontend Development

The frontend is built with Next.js 15, TypeScript, and Tailwind CSS with shadcn/ui components.

```bash
cd frontend
npm install
npm run dev
```

Key dependencies:

- Next.js for React framework
- Tailwind CSS for styling
- shadcn/ui for component library
- React Hook Form for form handling
- Zod for validation
- Recharts for data visualization

### Backend Development

The backend is built with Python Flask.

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Key features:

- RESTful API endpoints
- MongoDB database integration
- Data processing and transformation
- User authentication and authorization

### LLM Backend Development

The LLM backend provides AI-powered functionality using the Groq API.

```bash
cd llm-backend
pip install -r requirements.txt
python app.py
```

Key features:

- Query processing pipeline
- Chart and report generation
- Natural language classification
- Asynchronous task processing

### Docker

The application is containerized with Docker, with each service having its own container:

- MongoDB database
- Backend Flask API
- LLM Backend API
- Frontend Next.js application
- Nginx for routing

The Docker Compose file orchestrates these containers and manages networking and volumes.

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

Project Link: [https://github.com/RecceLabTechies/LLM-Powered-Dashboard](https://github.com/RecceLabTechies/LLM-Powered-Dashboard)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

- [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
- [Tailwind CSS](https://tailwindcss.com)
- [shadcn/ui](https://ui.shadcn.com/)
- [Next.js](https://nextjs.org/)
- [Flask](https://flask.palletsprojects.com/)
- [MongoDB](https://www.mongodb.com/)
- [Groq API](https://groq.com/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/reccelabtechies/FullStack.svg?style=for-the-badge
[contributors-url]: https://github.com/RecceLabTechies/LLM-Powered-Dashboard/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/reccelabtechies/FullStack.svg?style=for-the-badge
[forks-url]: https://github.com/RecceLabTechies/LLM-Powered-Dashboard/network/members
[stars-shield]: https://img.shields.io/github/stars/reccelabtechies/FullStack.svg?style=for-the-badge
[stars-url]: https://github.com/RecceLabTechies/LLM-Powered-Dashboard/stargazers
[issues-shield]: https://img.shields.io/github/issues/reccelabtechies/FullStack.svg?style=for-the-badge
[issues-url]: https://github.com/RecceLabTechies/LLM-Powered-Dashboard/issues
[license-shield]: https://img.shields.io/github/license/reccelabtechies/FullStack.svg?style=for-the-badge
[license-url]: https://github.com/RecceLabTechies/LLM-Powered-Dashboard/blob/master/LICENSE
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Python.org]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://python.org/
[Flask.com]: https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white
[Flask-url]: https://flask.palletsprojects.com/
[MongoDB.com]: https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white
[MongoDB-url]: https://www.mongodb.com/
[TailwindCSS.com]: https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white
[TailwindCSS-url]: https://tailwindcss.com/
[Docker.com]: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://docker.com/
