from extra_checks.utils import collect_subclasses


def test_collect_subclasses():
    """test that we collect all descendants"""

    class Base:
        pass

    class One(Base):
        pass

    class Two(Base):
        pass

    class Three(One, Two):
        pass

    serializers = collect_subclasses(Base.__subclasses__())
    assert set(serializers) == {One, Two, Three}
