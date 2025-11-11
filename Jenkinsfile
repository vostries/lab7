pipeline {
    agent {
        docker {
            image 'python:3.9-slim'
            args '--privileged -v /dev:/dev --network host'
        }
    }
    
    environment {
        BMC_IMAGE = '/var/jenkins_home/romulus/obmc-phosphor-image-romulus-20250903025632.static.mtd'
        BMC_IP = 'localhost'
        BMC_PORT = '2443'
        SSH_PORT = '2222'
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
                sh 'echo "Repository content:" && ls -la'
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    echo "Setting up testing environment..."
                    sh '''
                        apt update
                        apt install -y qemu-system-arm python3-pip curl wget net-tools
                        pip install requests pytest selenium locust urllib3 pytest-html
                        
                        # Install Chrome for WebUI tests
                        apt install -y gnupg wget unzip
                        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
                        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
                        apt update
                        apt install -y google-chrome-stable
                        
                        # Install ChromeDriver
                        CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
                        CHROME_MAJOR=${CHROME_VERSION%%.*}
                        wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}"
                        CHROME_DRIVER_VERSION=$(cat LATEST_RELEASE_${CHROME_MAJOR})
                        wget -q "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip"
                        unzip chromedriver_linux64.zip
                        mv chromedriver /usr/local/bin/
                        chmod +x /usr/local/bin/chromedriver
                        
                        echo "=== Environment Setup Complete ==="
                    '''
                }
            }
        }
        
        stage('Start OpenBMC in QEMU') {
            steps {
                script {
                    echo "Starting OpenBMC in QEMU..."
                    sh """
                        # Kill any existing QEMU processes
                        pkill -f qemu-system-arm || true
                        sleep 2
                        
                        echo "BMC image path: ${env.BMC_IMAGE}"
                        ls -la ${env.BMC_IMAGE} || echo "WARNING: BMC image might not be accessible"
                        
                        # Start QEMU with OpenBMC
                        qemu-system-arm -m 256 -M romulus-bmc -nographic \\
                          -drive file=${env.BMC_IMAGE},format=raw,if=mtd \\
                          -net nic -net user,hostfwd=tcp::${env.SSH_PORT}-:22,hostfwd=tcp::${env.BMC_PORT}-:443,hostfwd=udp::2623-:623,hostname=qemu &
                        
                        QEMU_PID=\$!
                        echo \$QEMU_PID > qemu.pid
                        echo "QEMU started with PID: \$QEMU_PID"
                        
                        # Wait for BMC to boot
                        echo "Waiting for BMC to start (90 seconds)..."
                        sleep 90
                        
                        # Test BMC connectivity
                        echo "Testing BMC connectivity..."
                        for i in {1..12}; do
                            if curl -k https://${env.BMC_IP}:${env.BMC_PORT}/redfish/v1 2>/dev/null; then
                                echo "BMC is ready!"
                                break
                            else
                                echo "Attempt \$i: BMC not ready, waiting 10 seconds..."
                                sleep 10
                            fi
                        done
                    """
                }
            }
        }
        
        stage('Run API Autotests') {
            steps {
                script {
                    echo "Running API autotests..."
                    dir('tests') {
                        sh '''
                            # Просто запускаем тесты - все файлы уже есть в репозитории
                            python -m pytest test_redfish.py -v --junitxml=../api-test-results.xml
                        '''
                    }
                }
            }
            post {
                always {
                    junit 'api-test-results.xml'
                    archiveArtifacts artifacts: 'api-test-results.xml', fingerprint: true
                }
            }
        }
        
        stage('Run WebUI Tests') {
            steps {
                script {
                    echo "Running WebUI tests..."
                    dir('tests') {
                        sh '''
                            # Set up virtual display for Chrome
                            export DISPLAY=:99
                            Xvfb :99 -screen 0 1920x1080x24 &
                            XVFB_PID=$!
                            
                            # Просто запускаем WebUI тесты - все файлы уже есть
                            python test.py 2>&1 | tee ../webui-test-output.log
                            TEST_EXIT_CODE=${PIPESTATUS[0]}
                            
                            # Kill Xvfb
                            kill $XVFB_PID 2>/dev/null || true
                            
                            exit $TEST_EXIT_CODE
                        '''
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'webui-test-output.log', fingerprint: true
                }
            }
        }
        
        stage('Run Load Testing') {
            steps {
                script {
                    echo "Running load tests with Locust..."
                    dir('tests') {
                        sh '''
                            # Просто запускаем нагрузочное тестирование - locustfile.py уже есть
                            locust -f locustfile.py --headless -u 5 -r 1 -t 30s --html=../load-test-report.html
                        '''
                    }
                }
            }
            post {
                always {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'load-test-report.html',
                        reportName: 'Load Test Report'
                    ])
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "Cleaning up..."
                sh '''
                    # Stop QEMU
                    if [ -f qemu.pid ]; then
                        echo "Stopping QEMU..."
                        kill $(cat qemu.pid) 2>/dev/null || true
                        sleep 5
                        rm -f qemu.pid
                    fi
                    
                    # Clean up any remaining processes
                    pkill -f qemu-system-arm || true
                    pkill -f Xvfb || true
                '''
            }
            
            // Archive all test results
            archiveArtifacts artifacts: '**/*.xml, **/*.log, **/*.html', fingerprint: true
            
            // Clean workspace
            cleanWs()
        }
        success {
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed!"
        }
    }
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }
}