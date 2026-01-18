class DestroyCommand:
    """Destroy APUS deployed modules."""

    def __init__(
        self,
        session,
        stack_name: str,
    ):
        self.session = session
        self.stack_name = stack_name

    def execute(self):
        print('Destroying resources...')
