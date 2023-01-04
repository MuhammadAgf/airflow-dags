from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.kubernetes.secret import Secret
from kubernetes.client import models as k8s_models


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.utcnow(),
    'email': ['trainer@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

secret_volume = Secret(
    deploy_type="volume",
    deploy_target="/var/secrets/google",
    secret="google-cloud-keys",
    key="secret.json",
)

dag = DAG(
    'kubernetes_trainer',
    default_args=default_args,
    schedule_interval="0 0 * * *"
)


start = DummyOperator(task_id='start', dag=dag)

job = KubernetesPodOperator(
    namespace='default',
    image="m46f/mlops-demo-trainer:latest",
    name="airflow-train-text-model",
    task_id="train-text-model",
    secrets=[secret_volume],
    env_vars={
        "MODEL_FILE_NAME": "text-clf.joblib",
        "BUCKET_NAME": "morgana-mlops",
        "REMOTE_FILE_NAME": "demo/text-clf.joblib",
        "PROJECT_NAME": "camelot-420",
        "GOOGLE_APPLICATION_CREDENTIALS": "/var/secrets/google/secret.json",
    },
    container_resources=k8s_models.V1ResourceRequirements(
        requests={"memory": "500M", "cpu": "100m"}
    ),
    get_logs=True,
    dag=dag,
    image_pull_policy="Always",
)

end = DummyOperator(task_id='end', dag=dag)


job.set_upstream(start)
job.set_downstream(end)
