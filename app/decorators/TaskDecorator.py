import yaml
from clearml import Task


def load_params_from_yaml(yaml_file):
    #Загружает параметры из YAML файла
    try:
        with open(yaml_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Ошибка: Файл {yaml_file} не найден.")
        return {}
    except yaml.YAMLError as e:
        print(f"Ошибка при загрузке YAML: {e}")
        return {}


def cml_task(yaml_file=None, project_name=None, task_name=None, tags=None, artifacts=None):
    """
    Декоратор для инициализации задачи ClearML с параметрами из YAML.

    :param yaml_file: Путь к YAML файлу с параметрами.
    :param project_name: Имя проекта.
    :param task_name: Имя задачи.
    :param tags: Список тегов.
    :param artifacts: Артефакты для загрузки.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Загружаем параметры из YAML, если представлен файл
            if yaml_file:
                config_params = load_params_from_yaml(yaml_file)
                project_name_local = config_params.get('project_name', project_name)
                task_name_local = config_params.get('task_name', task_name or func.__name__)
                tags_local = config_params.get('tags', tags)
                artifacts_local = config_params.get('artifacts', artifacts)
            else:
                project_name_local = project_name
                task_name_local = task_name or func.__name__
                tags_local = tags
                artifacts_local = artifacts

            # Инициализация задачи
            task = Task.init(
                project_name=project_name_local,
                task_name=task_name_local,
                tags=tags_local or []
            )

            # Загружаем артефакты, если они были указаны
            if artifacts_local:
                _upload_artifacts(task, artifacts_local)

            return _execute_task(func, task, *args, **kwargs)

        return wrapper

    return decorator


def _upload_artifacts(task, artifacts):
    #Загружает артефакты в задачу.
    for artifact_name, artifact_value in artifacts.items():
        task.upload_artifact(name=artifact_name, artifact_object=artifact_value)


def _execute_task(func, task, *args, **kwargs):
    #Выполняет основную функцию и обрабатывает ошибки
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        task.get_logger().report_text(f"Error: {str(e)}")
        raise
    else:
        task.get_logger().report_text("Task completed successfully.")
        return result
    finally:
        task.close()
