// Jenkinsfile - Pipeline CI/CD pour Data Analysis Platform
// Déclarative Pipeline Syntax

pipeline {
    agent any
    
    // Variables d'environnement
    environment {
        PYTHON_VERSION = '3.11'
        VENV_DIR = 'venv'
        PROJECT_NAME = 'data-analysis-platform'
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/${env.DOCKER_USERNAME}/${PROJECT_NAME}"
        
        // Credentials (à configurer dans Jenkins)
        DOCKER_CREDENTIALS = credentials('docker-hub-credentials')
        REDIS_HOST = 'localhost'
        REDIS_PORT = '6379'
    }
    
    // Configuration des options
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }
    
    // Déclencheurs
    triggers {
        // Poll SCM toutes les 5 minutes
        pollSCM('H/5 * * * *')
        
        // Build automatique sur commit GitHub
        githubPush()
    }
    
    // Paramètres (optionnels)
    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['staging', 'production'],
            description: 'Environnement de déploiement'
        )
        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Ignorer les tests (non recommandé)'
        )
        booleanParam(
            name: 'DEPLOY',
            defaultValue: false,
            description: 'Déployer après le build'
        )
    }
    
    stages {
        // ====================================
        // STAGE 1: Checkout & Setup
        // ====================================
        stage('Checkout') {
            steps {
                echo '🔄 Récupération du code source...'
                checkout scm
                
                script {
                    // Récupérer les infos Git
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.GIT_BRANCH = env.BRANCH_NAME ?: 'unknown'
                }
                
                echo "📍 Branch: ${env.GIT_BRANCH}"
                echo "📍 Commit: ${env.GIT_COMMIT_SHORT}"
            }
        }
        
        // ====================================
        // STAGE 2: Setup Python Environment
        // ====================================
        stage('Setup Python') {
            steps {
                echo '🐍 Configuration environnement Python...'
                
                sh '''
                    # Vérifier la version Python
                    python3 --version
                    
                    # Créer environnement virtuel
                    python3 -m venv ${VENV_DIR}
                    
                    # Activer et installer les dépendances
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest pytest-cov black flake8 mypy
                '''
            }
        }
        
        // ====================================
        // STAGE 3: Code Quality Checks
        // ====================================
        stage('Code Quality') {
            parallel {
                stage('Black (Formatting)') {
                    steps {
                        echo '🎨 Vérification du formatage (Black)...'
                        sh '''
                            . ${VENV_DIR}/bin/activate
                            black --check data_loader data_processor visualization api utils tests main.py config.py
                        '''
                    }
                }
                
                stage('Flake8 (Linting)') {
                    steps {
                        echo '🔍 Linting du code (Flake8)...'
                        sh '''
                            . ${VENV_DIR}/bin/activate
                            flake8 data_loader data_processor visualization api utils \
                                --max-line-length=100 \
                                --statistics \
                                --output-file=flake8-report.txt || true
                        '''
                        
                        // Publier le rapport
                        archiveArtifacts artifacts: 'flake8-report.txt', allowEmptyArchive: true
                    }
                }
                
                stage('MyPy (Type Checking)') {
                    steps {
                        echo '🔬 Vérification des types (MyPy)...'
                        sh '''
                            . ${VENV_DIR}/bin/activate
                            mypy data_loader data_processor visualization api utils \
                                --ignore-missing-imports \
                                --junit-xml mypy-report.xml || true
                        '''
                    }
                }
            }
        }
        
        // ====================================
        // STAGE 4: Start Redis (for tests)
        // ====================================
        stage('Start Redis') {
            steps {
                echo '🔴 Démarrage Redis pour les tests...'
                sh '''
                    # Vérifier si Redis est déjà en cours d'exécution
                    if ! pgrep -x "redis-server" > /dev/null; then
                        redis-server --daemonize yes --port ${REDIS_PORT}
                        sleep 2
                    fi
                    
                    # Tester la connexion
                    redis-cli -p ${REDIS_PORT} ping
                '''
            }
        }
        
        // ====================================
        // STAGE 5: Run Tests
        // ====================================
        stage('Tests') {
            when {
                expression { return !params.SKIP_TESTS }
            }
            
            steps {
                echo '🧪 Exécution des tests...'
                
                sh '''
                    . ${VENV_DIR}/bin/activate
                    
                    # Créer les répertoires nécessaires
                    mkdir -p data uploads outputs logs
                    
                    # Exécuter les tests avec couverture
                    pytest \
                        --cov=data_loader \
                        --cov=data_processor \
                        --cov=visualization \
                        --cov=api \
                        --cov-report=xml \
                        --cov-report=html \
                        --cov-report=term-missing \
                        --junitxml=junit.xml \
                        --verbose
                '''
            }
            
            post {
                always {
                    // Publier les résultats des tests
                    junit 'junit.xml'
                    
                    // Publier le rapport de couverture
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                    
                    // Archiver les rapports
                    archiveArtifacts artifacts: 'coverage.xml,junit.xml', allowEmptyArchive: true
                }
            }
        }
        
        // ====================================
        // STAGE 6: Security Scan
        // ====================================
        stage('Security Scan') {
            steps {
                echo '🔒 Scan de sécurité...'
                
                sh '''
                    . ${VENV_DIR}/bin/activate
                    
                    # Installer les outils de sécurité
                    pip install safety bandit
                    
                    # Scan des dépendances
                    safety check --json --output safety-report.json || true
                    
                    # Scan du code
                    bandit -r data_loader data_processor visualization api utils \
                        -f json -o bandit-report.json || true
                '''
                
                archiveArtifacts artifacts: 'safety-report.json,bandit-report.json', allowEmptyArchive: true
            }
        }
        
        // ====================================
        // STAGE 7: Build Docker Image
        // ====================================
        stage('Build Docker') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    expression { return params.DEPLOY }
                }
            }
            
            steps {
                echo '🐳 Build de l\'image Docker...'
                
                script {
                    // Tag de l'image
                    def imageTag = "${env.GIT_BRANCH}-${env.GIT_COMMIT_SHORT}"
                    env.DOCKER_IMAGE_TAG = "${DOCKER_IMAGE}:${imageTag}"
                    env.DOCKER_IMAGE_LATEST = "${DOCKER_IMAGE}:latest"
                    
                    // Build
                    sh """
                        docker build \
                            -t ${env.DOCKER_IMAGE_TAG} \
                            -t ${env.DOCKER_IMAGE_LATEST} \
                            --build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                            --build-arg VCS_REF=${env.GIT_COMMIT_SHORT} \
                            .
                    """
                }
            }
        }
        
        // ====================================
        // STAGE 8: Push Docker Image
        // ====================================
        stage('Push Docker') {
            when {
                anyOf {
                    branch 'main'
                    expression { return params.DEPLOY }
                }
            }
            
            steps {
                echo '📤 Push de l\'image Docker...'
                
                script {
                    // Login Docker Hub
                    sh """
                        echo ${DOCKER_CREDENTIALS_PSW} | docker login \
                            -u ${DOCKER_CREDENTIALS_USR} \
                            --password-stdin ${DOCKER_REGISTRY}
                    """
                    
                    // Push
                    sh """
                        docker push ${env.DOCKER_IMAGE_TAG}
                        docker push ${env.DOCKER_IMAGE_LATEST}
                    """
                }
            }
        }
        
        // ====================================
        // STAGE 9: Deploy (optionnel)
        // ====================================
        stage('Deploy') {
            when {
                allOf {
                    branch 'main'
                    expression { return params.DEPLOY }
                }
            }
            
            steps {
                echo "🚀 Déploiement vers ${params.DEPLOY_ENV}..."
                
                script {
                    if (params.DEPLOY_ENV == 'staging') {
                        // Déploiement staging
                        sh '''
                            # Exemple: SSH vers serveur staging
                            # ssh user@staging-server "cd /app && docker-compose pull && docker-compose up -d"
                            echo "Déploiement staging simulé"
                        '''
                    } else if (params.DEPLOY_ENV == 'production') {
                        // Déploiement production (avec confirmation)
                        input message: 'Confirmer le déploiement en PRODUCTION?', ok: 'Déployer'
                        
                        sh '''
                            # Exemple: Déploiement Kubernetes
                            # kubectl set image deployment/data-analysis-api api=${DOCKER_IMAGE_TAG}
                            echo "Déploiement production simulé"
                        '''
                    }
                }
            }
        }
    }
    
    // ====================================
    // POST ACTIONS
    // ====================================
    post {
        always {
            echo '🧹 Nettoyage...'
            
            // Arrêter Redis
            sh 'redis-cli -p ${REDIS_PORT} shutdown || true'
            
            // Nettoyer les fichiers temporaires
            sh '''
                rm -rf uploads/* outputs/* logs/*
                rm -rf ${VENV_DIR}
            '''
            
            // Nettoyer les images Docker locales (garde les 5 dernières)
            sh '''
                docker images ${DOCKER_IMAGE} --format "{{.ID}}" | tail -n +6 | xargs -r docker rmi || true
            '''
        }
        
        success {
            echo '✅ Build réussi!'
            
            // Notification Slack (optionnel)
            /*
            slackSend(
                color: 'good',
                message: "✅ Build #${env.BUILD_NUMBER} réussi - ${env.JOB_NAME}\nBranch: ${env.GIT_BRANCH}\nCommit: ${env.GIT_COMMIT_SHORT}"
            )
            */
        }
        
        failure {
            echo '❌ Build échoué!'
            
            // Notification d'échec
            /*
            slackSend(
                color: 'danger',
                message: "❌ Build #${env.BUILD_NUMBER} échoué - ${env.JOB_NAME}\nBranch: ${env.GIT_BRANCH}\nCommit: ${env.GIT_COMMIT_SHORT}\nLogs: ${env.BUILD_URL}"
            )
            */
            
            // Email aux développeurs
            /*
            emailext(
                subject: "Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Le build a échoué. Voir les logs: ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
            */
        }
        
        unstable {
            echo '⚠️ Build instable (tests échoués mais build réussi)'
        }
    }
}
