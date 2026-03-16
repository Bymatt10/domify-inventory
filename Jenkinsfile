pipeline {
    agent any

    environment {
        // Asegúrate de crear este ID de credencial en Jenkins de tipo 'Secret file'
        ENV_FILE = credentials('inventory-ronalds')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Preparar Configuración') {
            steps {
                // Copia las credenciales al archivo .env para ser usado por Docker Compose
                sh 'cp $ENV_FILE .env'
            }
        }

        stage('Desplegar Aplicación') {
            steps {
                script {
                    // Intenta usar 'docker compose' y si falla usa 'docker-compose'
                    def dockerCmd = sh(script: "docker compose version", returnStatus: true) == 0 ? "docker compose" : "docker-compose"
                    // Elimina los contenedores forzosamente si quedaron "huérfanos" o en uso por otro proceso
                    sh 'docker rm -f inventory_db inventory_web || true'
                    // Detiene y elimina contenedores anteriores del mismo proyecto
                    sh "${dockerCmd} down --remove-orphans"
                    sh "${dockerCmd} up -d --build"
                }
            }
        }
        
        stage('Verificar Estado') {
            steps {
                sh 'docker ps | grep inventory_web'
            }
        }
    }

    post {
        always {
            // Limpieza del archivo .env por seguridad
            sh 'rm -f .env'
        }
        success {
            echo '¡Domify Inventory desplegado con éxito!'
        }
        failure {
            echo 'El despliegue ha fallado. Revisa los logs de la consola.'
        }
    }
}
