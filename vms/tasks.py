from concurrent.futures import ThreadPoolExecutor


_pool_executor = ThreadPoolExecutor()


def creat_migrate_vm_task(task, **kwargs):
    try:
        future = _pool_executor.submit(task, **kwargs)
    except Exception as e:
        return e

    return future
