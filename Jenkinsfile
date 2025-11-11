pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    environment {
        REPORTS_DIR = "reports"
        REPO_URL = "https://github.com/vostries/lab7.git"
    }

    stages {

        stage('Clean Workspace') {
            steps {
                sh '''
                    echo "🧹 Cleaning workspace..."
                    rm -rf * .git* ${REPORTS_DIR} || true
                    mkdir -p ${REPORTS_DIR}
                '''
            }
        }

        stage('Git Clone') {
            steps {
                sh '''
                    echo "📦 Cloning repository..."
                    git clone --depth 1 ${REPO_URL} tmp_repo
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
                    echo "⚙️ Setting up environment..."
                    sudo apt update -y
                    sudo apt install -y python3-pip wget unzip xvfb curl gnupg --no-install-recommends

                    echo "🧩 Installing Google Chrome..."
                    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg
                    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
                    sudo apt update -y
                    sudo apt install -y google-chrome-stable

                    echo "🧩 Installing ChromeDriver via WebDriverManager..."
                    pip3 install --upgrade pip setuptools wheel
                    pip3 install selenium pytest requests locust webdriver-manager

                    echo "🧠 Checking Chrome installation..."
                    google-chrome --version || true

                    echo "✅ Environment setup completed successfully."
                '''
            }
        }


        stage('Start QEMU with OpenBMC') {
            steps {
                sh '''
                    echo "🚀 Starting QEMU with OpenBMC..."
                    sudo pkill -f qemu-system-arm || true
                    sleep 2

                    sudo qemu-system-arm -m 256 -M romulus-bmc -nographic \
                      -drive file=romulus/obmc-phosphor-image-romulus-20250903025632.static.mtd,format=raw,if=mtd \
                      -net nic -net user,hostfwd=tcp::2222-:22,hostfwd=tcp::2443-:443,hostfwd=udp::2623-:623,hostname=qemu &

                    QEMU_PID=$!
                    echo $QEMU_PID > qemu.pid
                    echo "QEMU started with PID: $QEMU_PID"

                    echo "⏳ Waiting for BMC to boot..."
                    sleep 90

                    echo "🔍 Testing BMC connectivity..."
                    for i in {1..10}; do
                        if curl -k https://localhost:2443/redfish/v1 2>/dev/null; then
                            echo "✅ BMC is ready!"
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
                    echo "🧪 Running API autotests..."
                    cd tests
                    python3 -m pytest test_redfish.py -v --junitxml=../${REPORTS_DIR}/api-test-results.xml
                '''
            }
            post {
                always {
                    junit "${REPORTS_DIR}/api-test-results.xml"
                }
            }
        }

        stage('Run WebUI Tests') {
            steps {
                sh '''
                    echo "🌐 Running WebUI Selenium tests..."
                    cd tests

                    # Используем webdriver-manager для автообновления ChromeDriver
                    python3 - <<'PYCODE'
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import subprocess, sys

# Настраиваем Chrome
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument('--allow-insecure-localhost')
chrome_options.add_argument('--disable-web-security')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

# Проверим, что Chrome и драйвер запускаются
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://example.com")
    print("✅ ChromeDriver successfully launched.")
    driver.quit()
except Exception as e:
    print(f"❌ Failed to start ChromeDriver: {e}")
    sys.exit(1)
PYCODE

                    echo "🚀 Starting main WebUI tests..."
                    xvfb-run -a python3 test.py 2>&1 | tee ../${REPORTS_DIR}/webui-test-output.log

                    TEST_RESULT=${PIPESTATUS[0]}
                    if [ ${TEST_RESULT} -ne 0 ]; then
                        echo "❌ WebUI tests failed!"
                        exit 1
                    else
                        echo "✅ WebUI tests passed successfully."
                    fi
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: "${REPORTS_DIR}/webui-test-output.log", fingerprint: true
                }
            }
        }

        stage('Run Load Testing') {
            steps {
                sh '''
                    echo "⚡ Running load testing with Locust..."
                    cd tests
                    python3 -m locust -f locustfile.py --headless -u 5 -r 1 -t 30s --html=../${REPORTS_DIR}/load-test-report.html
                '''
            }
            post {
                always {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: "${REPORTS_DIR}",
                        reportFiles: 'load-test-report.html',
                        reportName: 'Load Test Report'
                    ])
                }
            }
        }
    }

    post {
        always {
            echo "🧾 Build Status: ${currentBuild.currentResult}"
            sh '''
                if [ -f qemu.pid ]; then
                    sudo kill $(cat qemu.pid) 2>/dev/null || true
                    rm -f qemu.pid
                fi
                sudo pkill -f qemu-system-arm || true
            '''
            archiveArtifacts artifacts: '${REPORTS_DIR}/**/*', fingerprint: true
        }
    }
}
