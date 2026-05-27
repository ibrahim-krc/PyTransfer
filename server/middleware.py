import time
from server import core

class SpeedTrackerMiddleware:
    """
    WSGI Middleware to track upload and download speeds.
    It wraps the WSGI input stream for uploads, and the application iterable for downloads.
    """
    def __init__(self, app):
        self.app = app
        self.downloaded_bytes = 0
        self.uploaded_bytes = 0
        self.last_check_time = time.time()

    def update_speeds(self):
        now = time.time()
        dt = now - self.last_check_time
        if dt >= 1.0:
            core.transfer_stats["download_bytes_sec"] = self.downloaded_bytes / dt
            core.transfer_stats["upload_bytes_sec"] = self.uploaded_bytes / dt
            self.downloaded_bytes = 0
            self.uploaded_bytes = 0
            self.last_check_time = now

    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO', '')
        is_upload = path_info.startswith('/api/upload')
        is_download = path_info.startswith('/api/download')
        
        if is_upload:
            core.transfer_stats["active_uploads"] = core.transfer_stats.get("active_uploads", 0) + 1

        try:
            if 'wsgi.input' in environ:
                original_input = environ['wsgi.input']
                parent = self
                
                class InputWrapper:
                    def read(self, size=-1):
                        data = original_input.read(size)
                        parent.uploaded_bytes += len(data)
                        parent.update_speeds()
                        return data
                        
                    def readline(self, size=-1):
                        data = original_input.readline(size)
                        parent.uploaded_bytes += len(data)
                        parent.update_speeds()
                        return data
                        
                    def readlines(self, hint=-1):
                        lines = original_input.readlines(hint)
                        parent.uploaded_bytes += sum(len(line) for line in lines)
                        parent.update_speeds()
                        return lines
                        
                    def __iter__(self):
                        return self
                        
                    def __next__(self):
                        try:
                            line = next(original_input)
                            parent.uploaded_bytes += len(line)
                            parent.update_speeds()
                            return line
                        except StopIteration:
                            raise StopIteration
                            
                environ['wsgi.input'] = InputWrapper()

            # Disable wsgi.file_wrapper to force the server to iterate over the generator
            # so we can track the download speed chunk by chunk
            if 'wsgi.file_wrapper' in environ:
                del environ['wsgi.file_wrapper']

            # Call the original Flask app
            iterable = self.app(environ, start_response)
        finally:
            if is_upload:
                core.transfer_stats["active_uploads"] -= 1
        
        return self._generate(iterable, is_download)
        
    def _generate(self, iterable, is_download):
        if is_download:
            core.transfer_stats["active_downloads"] = core.transfer_stats.get("active_downloads", 0) + 1
            
        try:
            for data in iterable:
                self.downloaded_bytes += len(data)
                self.update_speeds()
                yield data
        finally:
            if is_download:
                core.transfer_stats["active_downloads"] -= 1
            # Ensure we always update at the end even if < 1s
            now = time.time()
            if now - self.last_check_time > 0:
                self.update_speeds()
                
            if hasattr(iterable, 'close'):
                iterable.close()
