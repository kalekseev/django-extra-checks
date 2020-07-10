from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy

_ = gettext_lazy


if True:
    # test that indentation doesn't break ast parser
    class Author(models.Model):
        first_name = models.CharField(max_length=100)
        last_name = models.CharField(max_length=100)


class Article(models.Model):
    site = models.ForeignKey(Site, verbose_name="site", on_delete=models.CASCADE)
    title = models.CharField("article title", max_length=100)
    text = models.TextField(verbose_name="article text")
    author = models.ForeignKey(
        Author, related_name="articles", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Site Article"


class NestedField(models.Field):
    """Resembles fields like postgres ArrayField."""

    def __init__(self, base_field, **kwargs):
        self.base_field = base_field
        super().__init__(**kwargs)


class ModelFieldVerboseName(models.Model):
    first_arg_name = models.CharField("first arg name [test]", max_length=32)
    kwarg_name = models.CharField(verbose_name="kwarg name [test]", max_length=32)
    arg_gettext = models.CharField(_("arg name [test]"), max_length=32)
    kwargs_gettext = models.CharField(
        verbose_name=_("kwarg name [test]"), max_length=32
    )
    gettext_case = models.CharField(verbose_name=_("Kwarg Name [test]"), max_length=32)
    gettext = models.CharField(
        verbose_name=gettext_lazy("kwarg name [test]"), max_length=32
    )
    name_related = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="name related test [X050]",
    )
    nested_field = NestedField(
        models.CharField(max_length=100), verbose_name="nested field [X050]"
    )
    no_name = models.CharField(max_length=32)
    no_name_related = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+"
    )
    no_name_nested_field = NestedField(models.CharField(max_length=100))


class ModelFieldHelpTextGettext(models.Model):
    text = models.CharField(max_length=10, help_text=_("my help text"))
    text_fail = models.CharField(max_length=10, help_text="my help text")


class ModelFieldFileUploadTo(models.Model):
    image = models.ImageField(upload_to="path/to/media")
    file = models.FileField(upload_to="path/to/files")
    image_fail = models.ImageField()
    file_fail = models.FileField()


class CustomTextField(models.TextField):
    pass


class ModelFieldTextNull(models.Model):
    text = models.TextField()
    chars = models.CharField(max_length=32)
    custom = CustomTextField()
    text_fail = models.TextField(null=True)
    chars_fail = models.CharField(null=True, max_length=32)
    custom_fail = CustomTextField(null=True)


class ModelFieldNullFalse(models.Model):
    myfield = models.IntegerField()
    myfield_fail = models.IntegerField(null=False)
    null_fail = models.NullBooleanField()


class ModelFieldNullDefault(models.Model):
    myfield = models.IntegerField(default=None)
    myfield_fail = models.IntegerField(null=True, default=None)


class ModelFieldForeignKeyIndex(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="+")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="+")
    another_article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+"
    )
    another_author = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+", db_index=True
    )
    field_one = models.ForeignKey(
        ModelFieldTextNull, on_delete=models.CASCADE, related_name="+", db_index=False
    )
    field_two = models.ForeignKey(
        ModelFieldNullFalse, on_delete=models.CASCADE, related_name="+", db_index=True
    )

    class Meta:
        unique_together = (("article", "author"), ("field_one", "field_two"))


class GenericKeyOne(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    service = GenericForeignKey("content_type", "object_id")


class GenericKeyTwo(models.Model):
    ones = GenericRelation("GenericKeyOne")
