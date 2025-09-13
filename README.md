# IRIS - Intelligent Recruitment Information System

**An AI-powered HR recruitment platform that automates CV evaluation and candidate ranking using OpenAI's GPT-4.**

![Python](https://img.shields.io/badge/python-v3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-v2.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Overview

IRIS is a modern HR recruitment management system that leverages artificial intelligence to streamline the hiring process. The platform automatically parses CVs, scores candidates against job requirements, and provides HR professionals with data-driven insights for making informed hiring decisions.

### 🎯 Key Features

- **🤖 AI-Powered CV Analysis**: Automatic parsing and intelligent scoring using OpenAI GPT-4
- **👥 Dual Role System**: Separate interfaces for HR professionals and job applicants
- **📄 Multi-Format CV Support**: PDF and DOCX file upload and processing
- **⚖️ Weighted Scoring**: Customizable evaluation criteria with adjustable weights
- **📊 Real-time Updates**: Live scoring updates using WebSocket technology
- **📈 Comprehensive Analytics**: Detailed scoring breakdowns and candidate rankings
- **🔒 Secure Authentication**: Role-based access control and secure user management
- **🐳 Docker Ready**: Containerized deployment for easy setup and scaling

## 🏗️ Architecture

### Technology Stack

- **Backend**: Flask (Python 3.10+)
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Real-time Communication**: Flask-SocketIO
- **AI Integration**: OpenAI GPT-4o API
- **File Processing**: PDFMiner (PDF), python-docx (DOCX)
- **Frontend**: Bootstrap + Jinja2 Templates
- **Deployment**: Docker & Docker Compose
- **Production Server**: Waitress WSGI

### Project Structure

```text
iris/
├── app.py                 # Flask application factory
├── models.py              # SQLAlchemy database models
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container configuration
├── docker-compose.yml    # Multi-container orchestration
├── forms.py              # WTForms for user input validation
├── utils.py              # Utility functions (CV parsing, AI scoring)
├── decorators.py         # Custom decorators for authorization
├── auth.py               # Authentication blueprint
├── hr.py                 # HR-specific routes and functionality
├── applicant.py          # Applicant-specific routes and functionality
├── static/               # Static assets (CSS, images, SCSS)
├── templates/            # Jinja2 HTML templates
│   ├── auth/            # Authentication templates
│   ├── hr/              # HR dashboard templates
│   └── applicant/       # Applicant dashboard templates
└── uploads/             # CV file storage directory
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (recommended)
- MySQL database
- OpenAI API key

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**

   ```bash
   git clone https://github.com/hasan0v/hris.git
   cd iris
   ```

2. **Create environment file**

   ```bash
   cp .env.example .env
   ```
   
   Configure your `.env` file:

   ```env
   SECRET_KEY=your-secret-key-here
   OPENAI_API_KEY=your-openai-api-key
   MYSQL_USER=your-mysql-username
   MYSQL_PASSWORD=your-mysql-password
   MYSQL_HOST=your-mysql-host
   MYSQL_PORT=3306
   MYSQL_DB=iris_db
   FLASK_ENV=development
   ```

3. **Start the application**

   ```bash
   docker-compose up --build
   ```

4. **Initialize the database**

   ```bash
   docker exec iris_web flask create-db
   ```

5. **Access the application**
   - Open your browser to `http://localhost:5000`

### Option 2: Local Development

1. **Clone and setup virtual environment**

   ```bash
   git clone https://github.com/hasan0v/hris.git
   cd iris
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   export SECRET_KEY=your-secret-key
   export OPENAI_API_KEY=your-openai-api-key
   # Add MySQL configuration variables
   ```

4. **Initialize database**

   ```bash
   flask create-db
   ```

5. **Run the application**

   ```bash
   flask run
   ```

## 📋 Usage Guide

### For HR Professionals

1. **Registration**
   - Register with HR role selection
   - Provide company information (optional)

2. **Create Job Vacancies**
   - Define job title and description
   - Set custom scoring weights for evaluation criteria:
     - Relevant Experience Years (default: 25%)
     - Technical Skills Match (default: 30%)
     - Education Level Relevance (default: 15%)
     - Project/Portfolio Quality (default: 10%)
     - Keyword Alignment (default: 10%)
     - Communication Clarity (default: 10%)

3. **Review Applications**
   - View automatically scored applications
   - Access detailed scoring breakdowns
   - Shortlist or reject candidates
   - Export candidate data to CSV

### For Job Applicants

1. **Registration**
   - Register as an applicant
   - Complete profile information

2. **CV Management**
   - Upload up to 5 CVs (PDF/DOCX, max 5MB each)
   - Delete outdated CVs
   - Track application history

3. **Apply for Positions**
   - Browse available vacancies
   - Apply with your most recent CV
   - Track application status and scores
   - Withdraw applications if needed

### AI Scoring System

The system evaluates CVs across six key dimensions:

1. **Relevant Experience Years**: Direct experience matching job requirements
2. **Technical Skills Match**: Alignment with required technical competencies
3. **Education Level Relevance**: Educational background suitability
4. **Project/Portfolio Quality**: Quality of demonstrated work and projects
5. **Keyword Alignment**: Relevant terminology and domain knowledge
6. **Communication Clarity**: CV structure, grammar, and presentation quality

Each dimension is scored 0.0-5.0, then weighted according to HR preferences to produce a final score.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask session encryption key | - | ✅ |
| `OPENAI_API_KEY` | OpenAI API access token | - | ✅ |
| `MYSQL_USER` | MySQL database username | - | ✅ |
| `MYSQL_PASSWORD` | MySQL database password | - | ✅ |
| `MYSQL_HOST` | MySQL server hostname | `localhost` | ✅ |
| `MYSQL_PORT` | MySQL server port | `3306` | ❌ |
| `MYSQL_DB` | Database name | `iris_db` | ❌ |
| `FLASK_ENV` | Flask environment mode | `production` | ❌ |
| `FLASK_DEBUG` | Enable debug mode | `0` | ❌ |

### File Upload Limits

- **Maximum file size**: 5MB per CV
- **Supported formats**: PDF, DOCX
- **Storage limit**: 5 CVs per applicant
- **Upload directory**: `./uploads/`

## 🛠️ API Documentation

### Authentication Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `GET /auth/logout` - User logout

### HR Endpoints

- `GET /hr/dashboard` - HR dashboard view
- `POST /hr/vacancy/new` - Create new vacancy
- `GET /hr/vacancy/<id>/applicants` - View applicants
- `POST /hr/application/shortlist/<id>` - Shortlist candidate
- `POST /hr/application/reject/<id>` - Reject candidate
- `GET /hr/vacancy/<id>/applicants/export` - Export CSV

### Applicant Endpoints

- `GET /applicant/dashboard` - Applicant dashboard
- `POST /applicant/cv/upload` - Upload CV
- `POST /applicant/apply/<vacancy_id>` - Apply for position
- `POST /applicant/application/withdraw/<id>` - Withdraw application
- `POST /applicant/cv/delete/<id>` - Delete CV

## 🎨 Customization

### Adding Custom Scoring Criteria

1. Update the `VacancyForm` in `forms.py` to include new weight fields
2. Modify the OpenAI prompt in `utils.py` to include new evaluation criteria
3. Update the database model and forms to handle new scoring dimensions

### Styling

- SCSS files located in `static/scss/`
- Compile with: `flask compile-sass`
- Bootstrap 5 framework for responsive design

## 🧪 Testing

### Manual Testing Commands

```bash
# Initialize fresh database
flask create-db

# Compile SCSS styles
flask compile-sass

# Clean up old uploaded files
flask cleanup-uploads --days 7
```

### Validation Checklist

- [ ] User registration and authentication
- [ ] CV upload (PDF and DOCX)
- [ ] Vacancy creation with custom weights
- [ ] Application submission and AI scoring
- [ ] Real-time score updates via WebSocket
- [ ] CSV export functionality
- [ ] Role-based access control

## 🚀 Deployment

### Production Considerations

1. **Security**
   - Use strong `SECRET_KEY`
   - Enable HTTPS
   - Configure CORS properly
   - Implement rate limiting

2. **Performance**
   - Use production WSGI server (Waitress included)
   - Configure database connection pooling
   - Implement caching for frequently accessed data
   - Monitor OpenAI API usage and costs

3. **Monitoring**
   - Set up application logging
   - Monitor file upload storage
   - Track API response times
   - Monitor OpenAI API costs

### Environment-Specific Settings

```python
# Production configuration example
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    # Add production-specific settings
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include error handling for external API calls
- Test both success and failure scenarios
- Update documentation for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for providing the GPT-4 API
- **Flask** ecosystem for the robust web framework
- **Bootstrap** for responsive UI components
- **PDFMiner** and **python-docx** for document parsing capabilities

## 📞 Support

For support and questions:

- Create an issue on GitHub
- Contact the development team
- Check the documentation for common solutions

---

Made with ❤️ for modern HR professionals