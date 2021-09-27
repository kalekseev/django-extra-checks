import pytest

try:
    import rest_framework.authtoken.serializers  # import AuthTokenSerializer into the project
    import rest_framework.serializers
except ImportError:
    pytest.skip("skipping rest_framework tests", allow_module_level=True)
from extra_checks.checks.drf_serializer_checks import (
    CheckDRFSerializerExtraKwargs,
    CheckDRFSerializerMetaAttribute,
    _collect_serializers,
    _get_serializers_to_check,
    check_drf_serializers,
)
from tests.example.serializers import (
    ArticleSerializer,
    AuthorSerializer,
    DisableCheckSerializer,
    ModernAuthorSerializer,
)


@pytest.fixture
def test_case(test_case):
    return test_case.handler(check_drf_serializers)


def test_collect_serializers():
    """test that we collect all descendants"""
    serializers = _collect_serializers([AuthorSerializer])
    assert set(serializers) == {AuthorSerializer, ModernAuthorSerializer}


def test_model_serializer_extra_kwargs(test_case):
    messages = (
        test_case.settings({"checks": [CheckDRFSerializerExtraKwargs.Id.value]})
        .check(CheckDRFSerializerExtraKwargs)
        .serializers(ArticleSerializer)
        .run()
    )
    assert not messages
    messages = test_case.serializers(AuthorSerializer).run()
    assert len(messages) == 1
    assert messages[0].id == CheckDRFSerializerExtraKwargs.Id.name


def test_model_serializer_meta_attribute(test_case):
    messages = (
        test_case.settings(
            {
                "checks": [
                    {
                        "id": CheckDRFSerializerMetaAttribute.Id.value,
                        "attrs": ["read_only_fields"],
                    }
                ]
            }
        )
        .check(CheckDRFSerializerMetaAttribute)
        .serializers(ArticleSerializer)
        .run()
    )
    assert not messages
    messages = test_case.serializers(AuthorSerializer).run()
    assert len(messages) == 1
    assert messages[0].id == CheckDRFSerializerMetaAttribute.Id.name


def test_get_serializers_to_check():
    ss, ms = _get_serializers_to_check()
    module = "tests.example.serializers"
    assert all(s.__module__ == module for s in ss)
    assert all(m.__module__ == module for m in ms)


def test_get_serializers_to_check_include_apps(settings):
    settings.INSTALLED_APPS += ["rest_framework.authtoken", "rest_framework"]
    ss, ms = (list(s) for s in _get_serializers_to_check(["rest_framework.authtoken"]))
    assert not ms
    assert len(ss) == 1
    assert ss[0] is rest_framework.authtoken.serializers.AuthTokenSerializer

    ss, ms = (list(s) for s in _get_serializers_to_check(["rest_framework"]))
    assert len(ms) == 1
    assert ms[0] is rest_framework.serializers.HyperlinkedModelSerializer
    # FIXME: the lines below actually a bug
    # include_apps must filter out rest_framework.authtoken app
    # but it's nested into rest_framework app that present in the
    # include_apps so it's included too
    assert len(ss) == 1
    assert ss[0] is rest_framework.authtoken.serializers.AuthTokenSerializer


def test_drf_ignore_meta_checks(test_case):
    messages = (
        test_case.settings({"checks": [CheckDRFSerializerExtraKwargs.Id.value]})
        .check(CheckDRFSerializerExtraKwargs)
        .serializers(DisableCheckSerializer)
        .run()
    )
    assert not messages
