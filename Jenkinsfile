pipeline {
    agent any
    
    options {
        skipDefaultCheckout(true)
    }
    
    stages {
        stage('Clean Workspace') {
            steps {
                sh 'rm -rf * .git* reports || true'
                sh 'mkdir -p reports'
            }
        }
        
        stage('Git Clone') {
            steps {
                sh '''
                    git clone --depth 1 https://github.com/vostries/lab7.git tmp_repo
                    mv tmp_repo/* .
                    mv tmp_repo/.* . 2>/dev/null || true
                    rm -rf tmp_repo
                    echo "=== Repository Content ==="
                    ls -la
                '''
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    echo "Installing dependencies..."
                    sudo apt update
                    sudo apt install -y python3-pip qemu-system-arm curl wget net-tools
                    
                    # Install Python packages
                    pip3 install requests pytest selenium locust urllib3 --break-system-packages
                    
                    # Install Chrome and ChromeDriver
                    sudo apt install -y chromium chromium-driver
                    sudo ln -sf /usr/bin/chromium /usr/bin/google-chrome
                    
                    echo "=== Environment setup completed ==="
                '''
            }
        }
        
        stage('Start QEMU with OpenBMC') {
            steps {
                sh '''
                    echo "Starting QEMU with OpenBMC..."
                    sudo pkill -f qemu-system-arm || true
                    sleep 2
                    
                    sudo qemu-system-arm -m 256 -M romulus-bmc -nographic \
                      -drive file=romulus/obmc-phosphor-image-romulus-20250903025632.static.mtd,format=raw,if=mtd \
                      -net nic -net user,hostfwd=tcp::2222-:22,hostfwd=tcp::2443-:443,hostfwd=udp::2623-:623,hostname=qemu &
                    
                    QEMU_PID=$!
                    echo $QEMU_PID > qemu.pid
                    echo "QEMU started with PID: $QEMU_PID"
                    
                    echo "Waiting for BMC to boot..."
                    sleep 90
                    
                    echo "Testing BMC connectivity..."
                    for i in {1..10}; do
                        if curl -k https://localhost:2443/redfish/v1 2>/dev/null; then
                            echo "BMC is ready!"
                            break
                        else
                            echo "⏳ Attempt $i: Waiting..."
                            sleep 10
                        fi
                    done
                '''
            }
        }
        
        stage('Run API Autotests') {
            steps {
                sh '''
                    echo "Running API Autotests..."
                    cd tests
                    python3 -m pytest test_redfish.py -v --junitxml=../reports/api-test-results.xml
                '''
            }
            post {
                always {
                    junit 'reports/api-test-results.xml'
                }
            }
        }
        
        stage('Run WebUI Tests') {
            steps {
                sh '''
                    echo "Running WebUI Tests..."
                    cd tests
                    
                    # Use webdriver-manager for automatic ChromeDriver management
                    pip3 install webdriver-manager --break-system-packages
                    
                    # Run WebUI tests
                    python3 test.py 2>&1 | tee ../reports/webui-test-output.log
                    
                    # Check exit code
                    if [ $? -eq 0 ]; then
                        echo "WebUI tests passed"
                    else
                        echo "WebUI tests failed"
                        exit 1
                    fi
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/webui-test-output.log', fingerprint: true
                }
            }
        }
        
        stage('Run Load Testing') {
            steps {
                sh '''
                    echo "Running Load Testing..."
                    cd tests
                    python3 -m locust -f locustfile.py --headless -u 5 -r 1 -t 30s --html=../reports/load-test-report.html
                '''
            }
            post {
                always {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports',
                        reportFiles: 'load-test-report.html',
                        reportName: 'Load Test Report'
                    ])
                }
            }
        }
    }
    
    post {
        always {
            echo "Build Status: ${currentBuild.currentResult}"
            sh '''
                if [ -f qemu.pid ]; then
                    sudo kill $(cat qemu.pid) 2>/dev/null || true
                    rm -f qemu.pid
                fi
                sudo pkill -f qemu-system-arm || true
            '''
            archiveArtifacts artifacts: 'reports/**/*', fingerprint: true
        }
    }
}