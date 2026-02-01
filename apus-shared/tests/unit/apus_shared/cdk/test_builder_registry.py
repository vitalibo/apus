from apus_shared.cdk import builder_registry


class TestStackBuilder(builder_registry.Builder):
    def build(self, stack, resources):
        pass


def test_registry(subtests):
    with subtests.test('empty'):
        assert builder_registry.builders == []

    with subtests.test('register'):
        builder_registry.register(TestStackBuilder())

        assert len(builder_registry.builders) == 1
