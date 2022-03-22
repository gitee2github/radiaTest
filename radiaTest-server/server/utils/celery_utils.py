from celery import Celery
from celeryservice import celeryconfig


def make_celery(app_name):
    broker = celeryconfig.broker_url
    backend = celeryconfig.result_backend

    celery = Celery(
        app_name,
        broker=broker,
        backend=backend,
        task_routes={
            'celeryservice.tasks.async_update_celerytask_status': {
                'queue': 'queue_update_celerytask_status',
                'routing_key': 'celerytask_status',
                'delivery_mode': 1,
            },
            'celeryservice.tasks.async_check_vmachine_lifecycle': {
                'queue': 'queue_check_vmachine_lifecycle',
                'routing_key': 'vmachine_lifecycle',
                'delivery_mode': 1,
            },
            'celeryservice.tasks.async_read_git_repo': {
                'queue': 'queue_read_git_repo',
                'routing_key': 'git_repo',
                'delivery_mode': 1,
            },
            'celeryservice.tasks.load_scripts': {
                'queue': 'queue_load_scripts',
                'routing_key': 'load_scripts',
                'delivery_mode': 1,
            },
            'celeryservice.sub_tasks.update_suite': {
                'queue': 'queue_update_suite',
                'routing_key': 'suite',
                'delivery_mode': 1,
            },
            'celeryservice.sub_tasks.update_case': {
                'queue': 'queue_update_case',
                'routing_key': 'case',
                'delivery_mode': 1,
            },
            'celeryservice.tasks.run_suite': {
                'queue': 'queue_run_suite',
                'routing_key': 'run_suite',
                'delivery_mode': 1,
            },
            'celeryservice.tasks.run_template': {
                'queue': 'queue_run_template',
                'routing_key': 'run_template',
                'delivery_mode': 1,
            },
            'celeryservice.sub_tasks.job_result_callback': {
                'queue': 'queue_job_callback',
                'routing_key': 'job_callback',
                'delivery_mode': 1,
            },
            'celeryservice.sub_tasks.run_case': {
                'queue': 'queue_run_case',
                'routing_key': 'run_case',
                'delivery_mode': 1,
            },
            'celeryservice.tasks.resolve_testcase_file': {
                'queue': 'queue_file_resolution',
                'routing_key': 'file',
                'delivery_mode': 1,
            },
            'celeryservice.tasks.resolve_testcase_file_for_baseline': {
                'queue': 'queue_file_resolution',
                'routing_key': 'file',
                'delivery_mode': 1,
            },
            'celeryservice.tasks.resolve_testcase_set': {
                'queue': 'queue_set_resolution',
                'routing_key': 'set',
                'delivery_mode': 1,
            },
        }
    )

    return celery


def init_celery(celery, app):
    """
    initial celery object wraps the task execution in an application context
    """
    celery.config_from_object(celeryconfig)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwds):
            with app.app_context():
                return self.run(*args, **kwds)

    celery.Task = ContextTask