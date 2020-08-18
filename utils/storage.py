import os
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import SuspiciousFileOperation


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise SuspiciousFileOperation(
                'Storage can not find an available filename for "%s". '
                'Please make sure that the corresponding file field '
                'allows sufficient "max_length".' % name
            )
        full_path = self.path(name)
        if self.exists(full_path):
            os.remove(full_path)

        return name


