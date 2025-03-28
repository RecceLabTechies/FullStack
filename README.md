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

<h3 align="center">FullStack Application</h3>

  <p align="center">
    A full-stack application with a Next.js frontend, Flask backend, LLM integration, and MongoDB database.
    <br />
    <a href="https://github.com/reccelabtechies/FullStack"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/reccelabtechies/FullStack">View Demo</a>
    &middot;
    <a href="https://github.com/reccelabtechies/FullStack/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/reccelabtechies/FullStack/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
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

This project is a modern web application designed with a microservices architecture, featuring:

- **Frontend**: Next.js with TypeScript, Tailwind CSS, and shadcn/ui components
- **Backend API**: Python Flask API server
- **LLM Backend**: Dedicated LLM service using Ollama models
- **Database**: MongoDB for data storage

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
- Node.js (for local frontend development)
- Python 3.8+ (for local backend development)
- Ollama (for LLM functionality)

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/reccelabtechies/FullStack.git
   ```
2. Make the startup script executable
   ```sh
   chmod +x start_app.sh
   ```
3. Start the application
   ```sh
   ./start_app.sh
   ```
4. The script will:
   - Check if Docker is running
   - Verify required Ollama models are installed
   - Start all services (MongoDB, Backend API, Frontend, LLM Backend)
5. Access the application
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5001
   - LLM Backend: Default port on your local machine

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Usage

The application can be stopped using the stop script:

```bash
./stop_app.sh
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- PROJECT STRUCTURE -->

## Project Structure

```
.
├── frontend/             # Next.js frontend application
├── backend/              # Flask API backend server
├── llm-backend/          # LLM service backend
├── mongodb-init/         # MongoDB initialization scripts
├── docker-compose.yml    # Docker compose configuration
├── start_app.sh          # Application startup script
└── stop_app.sh           # Application shutdown script
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- DEVELOPMENT -->

## Development

### Frontend Development

The frontend is built with Next.js 15, TypeScript, and Tailwind CSS.

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
python run.py
```

### LLM Backend Development

The LLM backend provides AI-powered functionality using Ollama models.

```bash
cd llm-backend
pip install -r requirements.txt
python app.py
```

### Docker

The application is containerized with Docker, with each service having its own container:

- MongoDB database
- Backend Flask API
- Frontend Next.js application

The Docker Compose file orchestrates these containers and manages networking and volumes.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->

## Roadmap

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3
  - [ ] Nested Feature

See the [open issues](https://github.com/reccelabtechies/FullStack/issues) for a full list of proposed features (and known issues).

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

### Top contributors:

<a href="https://github.com/reccelabtechies/FullStack/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=reccelabtechies/FullStack" alt="contrib.rocks image" />
</a>

<!-- LICENSE -->

## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

Javian Ng - [@javianng](https://github.com/javianng)

Project Link: [https://github.com/reccelabtechies/FullStack](https://github.com/reccelabtechies/FullStack)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

- [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
- [Img Shields](https://shields.io)
- [Choose an Open Source License](https://choosealicense.com)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/reccelabtechies/FullStack.svg?style=for-the-badge
[contributors-url]: https://github.com/reccelabtechies/FullStack/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/reccelabtechies/FullStack.svg?style=for-the-badge
[forks-url]: https://github.com/reccelabtechies/FullStack/network/members
[stars-shield]: https://img.shields.io/github/stars/reccelabtechies/FullStack.svg?style=for-the-badge
[stars-url]: https://github.com/reccelabtechies/FullStack/stargazers
[issues-shield]: https://img.shields.io/github/issues/reccelabtechies/FullStack.svg?style=for-the-badge
[issues-url]: https://github.com/reccelabtechies/FullStack/issues
[license-shield]: https://img.shields.io/github/license/reccelabtechies/FullStack.svg?style=for-the-badge
[license-url]: https://github.com/reccelabtechies/FullStack/blob/master/LICENSE
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Python.org]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Flask.com]: https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white
[Flask-url]: https://flask.palletsprojects.com/
[MongoDB.com]: https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white
[MongoDB-url]: https://www.mongodb.com/
[TailwindCSS.com]: https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white
[TailwindCSS-url]: https://tailwindcss.com/
[Docker.com]: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
