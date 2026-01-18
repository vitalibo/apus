from pathlib import Path


class DeployCommand:
    """Deploy APUS modules into AWS cloud."""

    def __init__(self, session, stack_name: str, files: list[Path], tags: list[str]):
        self.session = session
        self.stack_name = stack_name
        self.files = files
        self.tags = tags

    def execute(self):
        print('Deploying application...')
        print('Stack Name:', self.stack_name)
        print('Manifest Files:', self.files)
        print('Tags:', self.tags)
