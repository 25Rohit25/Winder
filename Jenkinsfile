pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = '1'
        PYTHONPATH = '.'
        WINDCTRL_ENV = 'ci'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                    python3.12 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r backend/requirements.txt
                '''
            }
        }

        stage('Lint & Format') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pip install ruff
                    ruff check backend/ scripts/
                '''
            }
        }

        stage('Unit Testing & Exact Boundaries') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m pytest backend/tests/unit/ -v --junitxml=reports/unit-test-results.xml
                '''
            }
        }

        stage('Integration & Property Testing') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m pytest backend/tests/property/ backend/tests/integration/ -v
                '''
            }
        }

        stage('Regression Fault Detection') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m pytest backend/tests/regression/ -v
                '''
            }
        }

        stage('Synthetic Data Generation') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python scripts/generate_sample_data.py --out-dir=data
                '''
            }
        }

        stage('Controller Validation Pipeline') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python scripts/run_validation.py --all-baseline
                '''
            }
        }

        stage('Report Generation') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python scripts/generate_report.py data/baseline/normal_run.csv --author="Jenkins CI"
                '''
            }
        }

        stage('Build Frontend UI') {
            steps {
                dir('frontend') {
                    sh '''
                        npm ci
                        npm run build
                    '''
                }
            }
        }

        stage('Package Artifacts') {
            steps {
                archiveArtifacts artifacts: 'reports/generated/**/*', fingerprint: true
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/**/*.xml'
        }
        success {
            echo 'WindCtrl Validate pipeline succeeded. Certification report ready.'
        }
        failure {
            echo 'Controller validation failure detected. Audit rejected.'
        }
    }
}
