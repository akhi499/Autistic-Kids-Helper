pipeline {
    // Executes on any available Jenkins agent
    agent any 

    environment {
        // Sets up a virtual environment in the workspace
        VENV = "${WORKSPACE}/venv"
        PATH = "${VENV}/bin:$PATH"
    }

    stages {
        stage('Checkout') {
            steps {
                // Pulls the latest code from your Git repository
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                echo 'Creating Python Virtual Environment...'
                sh '''
                    python3 -m venv ${VENV}
                    . ${VENV}/bin/activate
                    pip install --upgrade pip
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing requirements...'
                sh '''
                    . ${VENV}/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Database Migrations') {
            steps {
                echo 'Running initial migrations for the test environment...'
                sh '''
                    . ${VENV}/bin/activate
                    python manage.py makemigrations
                    python manage.py migrate
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Executing Django Tests...'
                sh '''
                    . ${VENV}/bin/activate
                    python manage.py test simulator
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution complete.'
            // Optional: Add steps here to clean up workspace or send email notifications
            cleanWs()
        }
        success {
            echo 'Build and tests passed successfully!'
        }
        failure {
            echo 'Build failed. Check the logs for errors.'
        }
    }
}
