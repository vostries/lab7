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
                    echo "=== Tests Directory ==="
                    ls -la tests/
                    echo "=== Romulus Directory ==="
                    ls -la romulus/
                '''
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    echo "Installing dependencies..."
                    sudo apt update
                    sudo apt install -y python3-pip qemu-system-arm curl wget net-tools unzip xvfb
                    
                    # Install Chromium for ARM instead of Chrome
                    sudo apt install -y chromium chromium-driver
                    
                    # Create symlinks for compatibility with your tests
                    sudo ln -sf /usr/bin/chromium /usr/bin/google-chrome
                    sudo ln -sf /usr/bin/chromium-driver /usr/bin/chromedriver
                    
                    # Install Python packages using apt (системные пакеты)
                    sudo apt install -y python3-requests python3-pytest python3-selenium python3-locust python3-urllib3
                    
                    echo "=== Environment setup completed ==="
                    echo "Installed packages:"
                    which google-chrome && echo "Chrome (Chromium): ✅"
                    which chromedriver && echo "ChromeDriver: ✅"
                    which python3 && echo "Python3: ✅"
                    which qemu-system-arm && echo "QEMU: ✅"
                    python3 -c "import requests; print('Requests: ✅')"
                    python3 -c "import pytest; print('Pytest: ✅')"
                    python3 -c "import selenium; print('Selenium: ✅')"
                    python3 -c "import locust; print('Locust: ✅')"
                '''
            }
        }
        
        stage('Start QEMU with OpenBMC') {
            steps {
                sh '''
                    echo "Starting QEMU with OpenBMC..."
                    # Kill any existing QEMU processes
                    sudo pkill -f qemu-system-arm || true
                    sleep 2
                    
                    echo "Checking BMC image..."
                    ls -la romulus/obmc-phosphor-image-romulus-20250903025632.static.mtd
                    
                    # Start QEMU with image from repository
                    sudo qemu-system-arm -m 256 -M romulus-bmc -nographic \
                      -drive file=romulus/obmc-phosphor-image-romulus-20250903025632.static.mtd,format=raw,if=mtd \
                      -net nic -net user,hostfwd=tcp::2222-:22,hostfwd=tcp::2443-:443,hostfwd=udp::2623-:623,hostname=qemu &
                    
                    QEMU_PID=$!
                    echo $QEMU_PID > qemu.pid
                    echo "QEMU started with PID: $QEMU_PID"
                    
                    echo "Waiting for BMC to boot (90 seconds)..."
                    sleep 90
                    
                    # Test BMC connectivity
                    echo "Testing BMC connectivity..."
                    for i in {1..10}; do
                        if curl -k https://localhost:2443/redfish/v1 2>/dev/null; then
                            echo "✅ BMC is ready!"
                            break
                        else
                            echo "⏳ Attempt $i: BMC not ready, waiting 10 seconds..."
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
                    archiveArtifacts artifacts: 'reports/api-test-results.xml', fingerprint: true
                }
            }
        }
        
        stage('Run WebUI Tests') {
            steps {
                sh '''
                    echo "Running WebUI Tests..."
                    cd tests
                    
                    # Set up virtual display
                    export DISPLAY=:99
                    Xvfb :99 -screen 0 1920x1080x24 &
                    XVFB_PID=$!
                    
                    # Run WebUI tests
                    python3 test.py 2>&1 | tee ../reports/webui-test-output.log
                    TEST_EXIT_CODE=${PIPESTATUS[0]}
                    
                    # Kill Xvfb
                    kill $XVFB_PID 2>/dev/null || true
                    
                    exit $TEST_EXIT_CODE
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
                    echo "Stopping QEMU..."
                    sudo kill $(cat qemu.pid) 2>/dev/null || true
                    rm -f qemu.pid
                fi
                sudo pkill -f qemu-system-arm || true
                sleep 2
            '''
            
            archiveArtifacts artifacts: 'reports/**/*', fingerprint: true
        }
        success {
            echo "ALL TESTS PASSED SUCCESSFULLY"
            sh '''
                echo "Reports saved in 'reports/' directory:"
                ls -la reports/
            '''
        }
        failure {
            echo "TESTS FAILED"
        }
    }
}