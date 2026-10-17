pipeline {
    agent any

    environment {
        CI_VENV = ".jenkins_ci_venv"
        IMAGE_NAME = "securecare"
        IMAGE_TAG = "1.0"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "=== Stage 1: Checkout Source Code ==="
                checkout scm
            }
        }

        stage('Environment Validation') {
            steps {
                echo "=== Stage 2: Environment & Tool Validation ==="
                sh '''
                    echo "Checking Python..."
                    python3 --version
                    echo "Checking Docker..."
                    docker --version
                    docker ps
                '''
            }
        }

        stage('Python Dependencies') {
            steps {
                echo "=== Stage 3: Install Python Dependencies ==="
                sh '''
                    echo "Creating isolated virtual environment: ${CI_VENV}"
                    python3 -m venv "${CI_VENV}"
                    . "${CI_VENV}/bin/activate"
                    pip install --no-cache-dir --upgrade pip
                    pip install --no-cache-dir -r requirements.txt
                '''
            }
        }

        stage('Python Tests') {
            steps {
                echo "=== Stage 4: Run Python Automated Tests ==="
                sh '''
                    . "${CI_VENV}/bin/activate"
                    pytest -v --tb=short
                '''
            }
        }

        stage('Frontend and Docker Build') {
            steps {
                echo "=== Stage 5: Build Unified Docker Image (${IMAGE_NAME}:${IMAGE_TAG}) ==="
                sh '''
                    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
                    docker images "${IMAGE_NAME}"
                '''
            }
        }

        stage('Container Health Verification') {
            steps {
                echo "=== Stage 6: Container Smoke Test & Health Verification ==="
                sh '''
                    CONTAINER_NAME="securecare-ci-${BUILD_NUMBER}"
                    echo "Target container name: ${CONTAINER_NAME}"

                    cleanup() {
                        echo "=== Guaranteed Cleanup: Stopping and removing ${CONTAINER_NAME} ==="
                        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
                        docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
                    }
                    trap cleanup EXIT INT TERM

                    echo "Starting smoke test container..."
                    docker run -d --name "${CONTAINER_NAME}" \
                        -e SECRET_KEY="ci-test-pipeline-secret-key-32ch!" \
                        -p 0:8000 \
                        "${IMAGE_NAME}:${IMAGE_TAG}"

                    CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "${CONTAINER_NAME}")
                    echo "Container running at IP: ${CONTAINER_IP}"

                    echo "Polling health endpoint at http://${CONTAINER_IP}:8000/health ..."
                    HEALTH_OK=0
                    for i in $(seq 1 30); do
                        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${CONTAINER_IP}:8000/health" 2>/dev/null || echo "000")
                        if [ "${HTTP_STATUS}" = "200" ]; then
                            echo "Health check PASSED with HTTP 200 on attempt ${i}!"
                            HEALTH_OK=1
                            break
                        fi
                        echo "Waiting for container startup... (attempt ${i}/30, status: ${HTTP_STATUS})"
                        sleep 1
                    done

                    if [ "${HEALTH_OK}" -ne 1 ]; then
                        echo "ERROR: Health check failed after 30 attempts. Container logs:"
                        docker logs "${CONTAINER_NAME}"
                        exit 1
                    fi

                    echo "Smoke test successfully completed."
                '''
            }
        }
    }

    post {
        always {
            sh '''
                echo "=== Cleaning up temporary CI virtual environment ==="
                rm -rf "${CI_VENV}"
            '''
        }
        success {
            echo "SecureCare CI Pipeline SUCCESS!"
        }
        failure {
            echo "SecureCare CI Pipeline FAILED! Please inspect stage logs above."
        }
    }
}
