pipeline {
    agent any

    environment {
        VENV = "${WORKSPACE}\\venv"
        PYTHONUNBUFFERED = '1'
        DJANGO_SETTINGS_MODULE = 'sociable_backend.settings'
    }

    options {
        // Discard builds older than 30 days or more than 50 builds
        buildDiscarder(logRotator(daysToKeepStr: '30', numToKeepStr: '50'))
        // Timeout after 1 hour
        timeout(time: 1, unit: 'HOURS')
        // Disable concurrent builds
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                echo '📥 Checking out code...'
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                echo '🐍 Setting up Python virtual environment...'
                bat '''
                    python -m venv "%VENV%"
                    "%VENV%\\Scripts\\python.exe" -m pip install --upgrade pip setuptools wheel
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                echo '📦 Installing dependencies...'
                bat '''
                    "%VENV%\\Scripts\\pip.exe" install -r requirements.txt
                '''
            }
        }

        stage('Code Quality') {
            steps {
                echo '🔍 Running code quality checks...'
                bat '''
                    "%VENV%\\Scripts\\pip.exe" install flake8 black isort pylint
                    
                    echo "Running flake8..."
                    "%VENV%\\Scripts\\flake8.exe" simulator/ --count --statistics --exit-zero
                    
                    echo "Checking code formatting with black..."
                    "%VENV%\\Scripts\\black.exe" --check --diff simulator/ || exit /b 0
                    
                    echo "Sorting imports..."
                    "%VENV%\\Scripts\\isort.exe" --check-only --diff simulator/ --exit-code || exit /b 0
                '''
            }
        }

        stage('Database Setup') {
            steps {
                echo '🗄️ Setting up test database...'
                bat '''
                    "%VENV%\\Scripts\\python.exe" manage.py migrate --run-syncdb
                '''
            }
        }

        stage('Collect Static Files') {
            steps {
                echo '📁 Collecting static files (optional for CI/CD)...'
                bat '''
                    "%VENV%\\Scripts\\python.exe" manage.py collectstatic --noinput --clear 2>&1 || exit /b 0
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo '✅ Running tests...'
                bat '''
                    "%VENV%\\Scripts\\python.exe" manage.py test simulator --verbosity=2 --keepdb
                '''
            }
        }

        stage('Test Coverage') {
            steps {
                echo '📊 Generating test coverage report...'
                bat '''
                    "%VENV%\\Scripts\\pip.exe" install coverage
                    "%VENV%\\Scripts\\python.exe" -m coverage run --source=simulator manage.py test simulator
                    "%VENV%\\Scripts\\python.exe" -m coverage report
                    "%VENV%\\Scripts\\python.exe" -m coverage xml
                '''
            }
        }

        stage('Security Scan') {
            steps {
                echo '🔐 Running security scan...'
                bat '''
                    "%VENV%\\Scripts\\pip.exe" install safety bandit
                    
                    echo "Checking for known vulnerabilities..."
                    "%VENV%\\Scripts\\python.exe" -m safety check --exit-code 0 || exit /b 0
                    
                    echo "Running bandit security scan..."
                    "%VENV%\\Scripts\\bandit.exe" -r simulator/ -f json -o bandit-report.json || exit /b 0
                '''
            }
        }

        stage('Build Docker Image') {
            when {
                branch 'main'
            }
            steps {
                echo '🐳 Building Docker image...'
                bat '''
                    docker build -t sociable-backend:%BUILD_NUMBER% .
                    docker tag sociable-backend:%BUILD_NUMBER% sociable-backend:latest
                '''
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                echo '🚀 Deploying to staging...'
                bat '''
                    echo "Staging deployment would happen here"
                '''
            }
        }
    }

    post {
        always {
            echo '🧹 Cleaning up...'
            cleanWs()
        }
        
        success {
            echo '✅ Build succeeded!'
            // Send success notification
            // slackSend(channel: '#builds', color: 'good', message: "Build ${BUILD_NUMBER} succeeded")
        }
        
        failure {
            echo '❌ Build failed!'
            // Send failure notification
            // slackSend(channel: '#builds', color: 'danger', message: "Build ${BUILD_NUMBER} failed")
        }
        
        unstable {
            echo '⚠️ Build unstable (tests passed but quality issues)'
        }
    }
}