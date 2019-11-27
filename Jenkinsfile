node {
    try {
        stage('Clean') {
            sh "rm -rf .[^.] .??* *"
        }
        stage('Checkout') {
            checkout scm
        }
        stage('Tests') {
           sh "./tests/runtests.sh MODE=test_dialog"
           currentBuild.result = 'SUCCESS'
        }
        stage('Test_skills') {
           sh "./tests/runtests.sh MODE=test_skills"
           currentBuild.result = 'SUCCESS'
        }
        stage('CollectPredictions') {
           sh "./tests/runtests.sh MODE=infer_questions"
        }
        if (env.BRANCH_NAME == 'dev') {
            stage('Deploy Dev') {
               sh "./deploy.sh MODE=all TARGET=dev"
               currentBuild.result = 'SUCCESS'
            }
        }
        def tag = sh(returnStdout: true, script: "git tag --contains | head -1").trim()
        if (tag) {
            stage('CollectPredictions') {
               sh "./tests/runtests.sh MODE=infer_questions"
            }
            stage('Deploy Prod') {
                sh "./deploy.sh MODE=all TARGET=prod"
                currentBuild.result = 'SUCCESS'
            }
        }
    } catch(e) {
        currentBuild.result = 'FAILURE'
        echo "Caught exception: ${e}"
        throw e
    } finally {
        archiveArtifacts artifacts: 'tests/dream/output/*', fingerprint: true
        archiveArtifacts artifacts: 'skills/transfertransfo/tests/test_results.json', fingerprint: true
        sh "./tests/runtests.sh MODE=clean"
        def msg = "Build for ${env.BRANCH_NAME} has status ${currentBuild.result}\n${env.BUILD_URL}"
        if (currentBuild.result == 'FAILURE') {
            slackSend color: 'bad', message: msg
        } else {
            slackSend color: 'good', message: msg
        }
    }
}
